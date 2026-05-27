// Joshua Geoghegan
// Smart Hurley - TinyML Inference with BLE (CNN v1)
// 4 classes: idle, swing, impact, fake_hit
// Sends classification + peak_g + decay_lambda to Android app via BLE
//
// BLE payload: JSON string
// {"cls":2,"conf":94,"peakG":21.3,"lambda":45.2}
// cls: 0=idle, 1=swing, 2=impact, 3=fake_hit
// lambda: exponential decay rate of post-impact vibration (s^-1)
//         higher lambda = faster vibration decay = sweeter contact location
//
// Model: 1D CNN operating on raw (100, 6) IMU windows
// Input normalisation: per-channel mean/std from training set (CHANNEL_MEAN / CHANNEL_STD)
// Window: 100 samples at ~125 Hz effective rate = ~800 ms context

// IMU library for the BMI270 accelerometer and gyroscope on the Nano 33 BLE Sense Rev2
#include <Arduino_BMI270_BMM150.h>
// BLE library for advertising and notifying the Android app
#include <ArduinoBLE.h>
// TensorFlow Lite for Microcontrollers runtime
#include <TensorFlowLite.h>
#include <tensorflow/lite/micro/all_ops_resolver.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/schema/schema_generated.h>

// Trained 1D CNN model converted to a C byte array via xxd
#include "hurley_cnn_model.h"

// BLE Service and Characteristic UUIDs
// Standard HM-10 UUIDs used so the Android app can locate the correct GATT characteristic
#define BLE_SERVICE_UUID        "0000ffe0-0000-1000-8000-00805f9b34fb"
#define BLE_CHARACTERISTIC_UUID "0000ffe1-0000-1000-8000-00805f9b34fb"

// Configuration
// WINDOW_SIZE and NUM_CHANNELS are defined in hurley_cnn_model.h (100 and 6)

// Minimum softmax confidence required before a classification is acted on
const int   CONFIDENCE_THRESHOLD   = 80;
// Target sample period in milliseconds giving approximately 125 Hz
const int   SAMPLING_INTERVAL_MS   = 8;
// Accelerometer magnitude below this value is treated as the hurley being still
const float ACTIVITY_THRESHOLD     = 2.3f;
// Minimum time between Serial debug prints to avoid flooding the monitor
const unsigned long PRINT_COOLDOWN_MS  = 500;
// Minimum time between non-impact BLE notifications to avoid flooding the app
const unsigned long SEND_COOLDOWN_MS   = 500;
// Lockout period after a confirmed impact to prevent double counting the same strike
const unsigned long IMPACT_COOLDOWN_MS = 1500;

// Decay estimation: number of post-peak samples used in peak-relative method
// Must match DECAY_SAMPLES in analyse_hits.py and plot_decay_comparison.py
const int DECAY_SAMPLES = 15;

// Channel indices into the sample row stored in w_buf
// Order matches training data: ax ay az gx gy gz
const int CH_AX = 0, CH_AY = 1, CH_AZ = 2;
const int CH_GX = 3, CH_GY = 4, CH_GZ = 5;

// TFLite
// CNN is larger than the MLP - increase arena size to 48 KB
// Static memory block used by TFLite for tensors and scratch buffers
constexpr int TENSOR_ARENA_SIZE = 48 * 1024;
uint8_t tensor_arena[TENSOR_ARENA_SIZE];

// TFLite object pointers initialised in setup()
const tflite::Model*       tfl_model     = nullptr;
tflite::MicroInterpreter*  interpreter   = nullptr;
TfLiteTensor*              input_tensor  = nullptr;
TfLiteTensor*              output_tensor = nullptr;
// Loads all available TFLite micro ops so any layer type in the model is supported
tflite::AllOpsResolver     resolver;

// BLE
// GATT service and notify characteristic used to push JSON payloads to the Android app
BLEService        hurleyService(BLE_SERVICE_UUID);
BLECharacteristic classificationCharacteristic(BLE_CHARACTERISTIC_UUID,
                                               BLERead | BLENotify, 64);

// Window Buffers
// Raw circular buffer: WINDOW_SIZE x NUM_CHANNELS (100 x 6)
// New samples overwrite the oldest slot keeping a rolling 800 ms window
float w_buf[WINDOW_SIZE][NUM_CHANNELS];
// Write index into the circular buffer
int   w_idx   = 0;
// Set to true once the buffer has been filled at least once
bool  w_ready = false;

// Tracks the last class sent over BLE to avoid resending the same idle state repeatedly
int lastSentClassification = -1;
// Timestamps used by the send and impact cooldown logic
unsigned long last_send   = 0;
unsigned long last_impact = 0;

// Helpers

// Returns the accelerometer magnitude of the most recent sample in the circular buffer
// Used by the activity gate to skip inference when the hurley is stationary
float current_magnitude() {
  int last = (w_idx == 0) ? WINDOW_SIZE - 1 : w_idx - 1;
  float ax = w_buf[last][CH_AX];
  float ay = w_buf[last][CH_AY];
  float az = w_buf[last][CH_AZ];
  return sqrt(ax*ax + ay*ay + az*az);
}

// Scans the entire window and returns the highest accelerometer magnitude found
// Sent to the Android app as the peak G value for each classified event
float peak_acc_mag() {
  float peak = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) {
    float ax = w_buf[i][CH_AX];
    float ay = w_buf[i][CH_AY];
    float az = w_buf[i][CH_AZ];
    float m  = sqrt(ax*ax + ay*ay + az*az);
    if (m > peak) peak = m;
  }
  return peak;
}

// Peak-Relative Decay Estimator
// Finds the peak acceleration sample in the window, then computes the mean of
// the next DECAY_SAMPLES samples. Lambda = (peak / decay_mean) * 8.
//
// A clean sweet-spot strike damps vibration quickly -> post-peak mean is low
// -> high lambda. An off-centre hit allows vibration to persist -> post-peak
// mean stays high -> low lambda.
//
// Thresholds (matching Android app and analysis scripts):
//   lambda >= 25 -> Sweet Spot
//   lambda >= 15 -> Good Contact
//   lambda <  15 -> Off Centre
float estimate_decay_lambda() {
  // Build acc_mag array from circular buffer
  float acc_mag[WINDOW_SIZE];
  for (int i = 0; i < WINDOW_SIZE; i++) {
    float ax = w_buf[i][CH_AX];
    float ay = w_buf[i][CH_AY];
    float az = w_buf[i][CH_AZ];
    acc_mag[i] = sqrt(ax*ax + ay*ay + az*az);
  }

  // Find the index and value of the peak acceleration sample
  int   peak_idx = 0;
  float peak_val = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) {
    if (acc_mag[i] > peak_val) { peak_val = acc_mag[i]; peak_idx = i; }
  }

  // Mean of next DECAY_SAMPLES after the peak
  int decay_start = peak_idx + 1;
  int decay_end   = decay_start + DECAY_SAMPLES;
  if (decay_end > WINDOW_SIZE) decay_end = WINDOW_SIZE;
  int decay_n = decay_end - decay_start;
  // Peak was at the very end of the window so there are no decay samples available
  if (decay_n <= 0) return 80.0f;

  float decay_mean = 0.0f;
  for (int i = decay_start; i < decay_end; i++) decay_mean += acc_mag[i];
  decay_mean /= decay_n;

  // Avoid division by near zero which would produce an unrealistically large lambda
  if (decay_mean < 0.1f) return 80.0f;

  // Ratio of peak to post-peak mean scaled by 8 to produce the lambda value
  return (peak_val / decay_mean) * 8.0f;
}

// CNN Inference Preparation
// Normalises the raw window per-channel using CHANNEL_MEAN and CHANNEL_STD
// from the header file, then fills the input tensor in (WINDOW_SIZE, NUM_CHANNELS)
// order to match the training data layout.
void prepare_cnn_input() {
  for (int t = 0; t < WINDOW_SIZE; t++) {
    for (int c = 0; c < NUM_CHANNELS; c++) {
      // Subtract the training mean and divide by training std to match StandardScaler applied during training
      float normalised = (w_buf[t][c] - CHANNEL_MEAN[c]) / CHANNEL_STD[c];
      input_tensor->data.f[t * NUM_CHANNELS + c] = normalised;
    }
  }
}

// Setup
void setup() {
  // Turn on the built-in LED to show the board is powered and running setup
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);
  // Wait for the Serial monitor to connect before continuing
  while(!Serial);

  Serial.println("Smart Hurley - TinyML CNN Inference with BLE v1");
  Serial.println("Classes: idle / swing / impact / fake_hit");
  Serial.print("Window size        : "); Serial.print(WINDOW_SIZE);     Serial.println(" samples (~800ms)");
  Serial.print("Activity threshold : "); Serial.print(ACTIVITY_THRESHOLD); Serial.println("G");
  Serial.println("────────────────────────────────────");

  // Initialize IMU
  if(!IMU.begin()) { Serial.println("ERR: IMU init failed!"); while(1); }
  Serial.println("IMU OK");

  // Initialize BLE
  if(!BLE.begin()) { Serial.println("ERR: BLE init failed!"); while(1); }

  // Set the device name that will appear in the Android app scan list
  BLE.setDeviceName("Smart Hurl");
  BLE.setLocalName("Smart Hurl");
  BLE.setAdvertisedService(hurleyService);
  hurleyService.addCharacteristic(classificationCharacteristic);
  BLE.addService(hurleyService);
  // Write an empty JSON object as the initial characteristic value before any inference runs
  const uint8_t empty[] = {'{', '}'};
  classificationCharacteristic.writeValue(empty, 2);
  BLE.advertise();
  Serial.println("BLE OK - Waiting for connection...");

  // Load TFLite model from the byte array in hurley_cnn_model.h
  tfl_model = tflite::GetModel(hurley_model_data);
  // Verify the flatbuffer schema version matches the linked TFLite runtime
  if(tfl_model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("ERR: Model schema mismatch!"); while(1);
  }

  // Create the interpreter using the static tensor arena allocated above
  interpreter = new tflite::MicroInterpreter(
    tfl_model, resolver, tensor_arena, TENSOR_ARENA_SIZE
  );

  // Allocate memory for all tensors within the arena
  if(interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("ERR: AllocateTensors failed!"); while(1);
  }

  // Cache pointers to the input and output tensors for use in the main loop
  input_tensor  = interpreter->input(0);
  output_tensor = interpreter->output(0);

  // Print how much of the 48 KB arena is actually used by this model
  Serial.print("Arena used: ");
  Serial.print(interpreter->arena_used_bytes());
  Serial.println(" bytes");
  Serial.println("Running...\n");
}

// Main Loop
void loop() {
  // Timestamps used to enforce the sampling interval and Serial print cooldown
  static unsigned long last_sample = 0;
  static unsigned long last_print  = 0;

  // Keep the BLE stack alive and process any incoming connection events
  BLE.poll();

  // Enforce the 8 ms sampling interval to achieve approximately 125 Hz
  if(millis() - last_sample < SAMPLING_INTERVAL_MS) return;
  last_sample = millis();

  float ax, ay, az, gx, gy, gz;
  // Skip this cycle if either sensor does not have a fresh reading ready
  if(!IMU.accelerationAvailable() || !IMU.gyroscopeAvailable()) return;

  IMU.readAcceleration(ax, ay, az);
  IMU.readGyroscope(gx, gy, gz);

  // Store raw sample into circular buffer
  w_buf[w_idx][CH_AX] = ax;
  w_buf[w_idx][CH_AY] = ay;
  w_buf[w_idx][CH_AZ] = az;
  w_buf[w_idx][CH_GX] = gx;
  w_buf[w_idx][CH_GY] = gy;
  w_buf[w_idx][CH_GZ] = gz;

  // Advance the write index and wrap around once the buffer is full
  w_idx++;
  if(w_idx >= WINDOW_SIZE) { w_idx = 0; w_ready = true; }
  // Do not run inference until the buffer has been filled at least once
  if(!w_ready) return;

  // Activity gate - skip inference if device is still
  // If the hurley has not moved above the threshold send a single idle notification and return
  if(current_magnitude() < ACTIVITY_THRESHOLD) {
    if(millis() - last_print >= PRINT_COOLDOWN_MS) {
      Serial.println(">> idle  (still)");
      last_print = millis();
    }
    // Only write the idle JSON once rather than on every loop iteration
    if(BLE.connected() && lastSentClassification != 0) {
      const char* idleJson = "{\"cls\":0,\"conf\":0,\"peakG\":0.0,\"lambda\":0.0}";
      classificationCharacteristic.writeValue((const uint8_t*)idleJson, strlen(idleJson));
      lastSentClassification = 0;
    }
    return;
  }

  // Prepare CNN input tensor (normalise raw window per-channel)
  prepare_cnn_input();

  // Run inference
  if(interpreter->Invoke() != kTfLiteOk) {
    Serial.println("ERR: Inference failed!"); return;
  }

  // Find best class by scanning the softmax output for the highest probability
  float best_prob  = 0;
  int   best_class = 0;
  for(int i = 0; i < NUM_CLASSES; i++) {
    if(output_tensor->data.f[i] > best_prob) {
      best_prob  = output_tensor->data.f[i];
      best_class = i;
    }
  }

  // Compute peak G across the window and estimate lambda only for impact classifications
  float peak_g     = peak_acc_mag();
  float decay_lambda = (best_class == 2) ? estimate_decay_lambda() : 0.0f;

  // Convert softmax probability to integer percentage for the JSON payload
  int pct = (int)(best_prob * 100);

  // Send over BLE with cooldown timers
  if(BLE.connected()) {
    unsigned long now_ms = millis();
    // Require both impact class and a minimum peak G to confirm a real strike
    bool is_impact = (best_class == 2 && peak_g > 8.0);
    //bool is_impact = (best_class == 2);

    // Impact cooldown - prevents double-counting the same strike
    if(is_impact && (now_ms - last_impact) < IMPACT_COOLDOWN_MS) goto skip_send;
    if(is_impact) last_impact = now_ms;

    // General send cooldown for non-impact classes
    if(!is_impact && (now_ms - last_send) < SEND_COOLDOWN_MS) goto skip_send;
    last_send = now_ms;

    {
      char buf[64];
      int len;
      // Include the lambda value in the payload only for confirmed impact events
      if (best_class == 2) {
        len = snprintf(buf, sizeof(buf),
          "{\"cls\":%d,\"conf\":%d,\"peakG\":%.1f,\"lambda\":%.1f}",
          best_class, pct, peak_g, decay_lambda);
      } else {
        len = snprintf(buf, sizeof(buf),
          "{\"cls\":%d,\"conf\":%d,\"peakG\":%.1f,\"lambda\":0.0}",
          best_class, pct, peak_g);
      }
      classificationCharacteristic.writeValue((const uint8_t*)buf, len);
      lastSentClassification = best_class;
    }
    skip_send:;
  }

  // Serial debug output
  // Respect the print cooldown so the Serial monitor does not flood at 125 Hz
  if(millis() - last_print < PRINT_COOLDOWN_MS) return;
  last_print = millis();

  // Only print classifications that meet the confidence threshold
  if(pct >= CONFIDENCE_THRESHOLD) {
    Serial.print(">> ");
    Serial.print(CLASS_NAMES[best_class]);
    Serial.print("  ("); Serial.print(pct); Serial.print("%)");
    Serial.print("  peak:"); Serial.print(peak_g, 1); Serial.print("G");
    // Print the lambda value only when a confirmed impact is detected
    if(best_class == 2 && peak_g > 8.0) {
      Serial.print("  lambda:"); Serial.print(decay_lambda, 1); Serial.print("s^-1");
    }
    Serial.print("  BLE: ");
    Serial.print(BLE.connected() ? "Connected" : "No connection");
    // Print the full softmax distribution across all four classes for debugging
    Serial.print(" [");
    for(int i = 0; i < NUM_CLASSES; i++) {
      Serial.print(CLASS_NAMES[i]); Serial.print(":");
      Serial.print((int)(output_tensor->data.f[i]*100)); Serial.print("%");
      if(i < NUM_CLASSES-1) Serial.print("  ");
    }
    Serial.println("]");
  }
}