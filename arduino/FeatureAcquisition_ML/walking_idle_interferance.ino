/*
Joshua Geoghegan
2/6/2026

Orientation invariant walking vs idle detection using logistic regression.
Weight (w) = 1.263832
Bias (b)   = -1.244710
*/

#include <Arduino_BMI270_BMM150.h>
#include <math.h>

#define SAMPLE_RATE_HZ 50         // IMU sampling rate
#define WINDOW_SIZE 50            // Samples per feature window (~1 second)

const float w = 1.263832;       // Trained logistic regression weight
const float b = -1.244710;      // Trained logistic regression bias

// GLOBAL VARIABLES
float mag_buffer[WINDOW_SIZE];
int sampleIndex = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial);
  // Initilize IMU
  if (!IMU.begin()) {
    Serial.println("Failed to initialize BMI270 IMU");
    while (1);
  }

  Serial.println("Walking/Idle detection started");
}

void loop() {
  float ax, ay, az;

  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(ax, ay, az);

    // Compute magnitude
    float magnitude = sqrt(ax*ax + ay*ay + az*az);

    // Store in buffer
    mag_buffer[sampleIndex] = magnitude;
    sampleIndex++;

    if (sampleIndex >= WINDOW_SIZE) {
      // Compute mean magnitude
      float mag_mean = 0.0;
      for (int i = 0; i < WINDOW_SIZE; i++) {
        mag_mean += mag_buffer[i];
      }
      mag_mean /= WINDOW_SIZE;

      // Logistic regression inference
      float z = w * mag_mean + b;
      float prob = 1.0 / (1.0 + exp(-z));

      // Classification
      if (prob >= 0.5) {
        Serial.println("WALKING");
      } else {
        Serial.println("IDLE");
      }

      // Reset buffer
      sampleIndex = 0;
    }

    delay(1000 / SAMPLE_RATE_HZ);
  }
}
