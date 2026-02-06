/*
Joshua Geoghegan
2/6/2026

Magnitude based feature extraction for motion classification.
Orientation invariant design using acceleration magnitude only.

*/

#include <Arduino_BMI270_BMM150.h>
#include <math.h>

#define SAMPLE_RATE_HZ 50        // IMU sampling rate
#define WINDOW_SIZE 50           // Samples per feature window (~1 second)

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

  Serial.println("BMI270 initialized");
  Serial.println("Magnitude-only feature acquisition started");
}

void loop() {

  float ax, ay, az;

  if (IMU.accelerationAvailable()) {

    // Read acceleration (in g)
    IMU.readAcceleration(ax, ay, az);

    // Compute acceleration magnitude
    float magnitude = sqrt(ax * ax + ay * ay + az * az);

    // Store magnitude sample
    mag_buffer[sampleIndex] = magnitude;
    sampleIndex++;

    // When window is full compute feature
    if (sampleIndex >= WINDOW_SIZE) {

      float mag_mean = 0.0;

      for (int i = 0; i < WINDOW_SIZE; i++) {
        mag_mean += mag_buffer[i];
      }

      mag_mean /= WINDOW_SIZE;

      // Output feature (easy for the Python parsing)
      Serial.print("FEATURE: ");
      Serial.println(mag_mean, 4);

      // Reset for next window
      sampleIndex = 0;
    }

    delay(1000 / SAMPLE_RATE_HZ);
  }
}
