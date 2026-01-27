// Joshua Geoghegan
// 1/27/2026

/*
   This sketch reads accelerometer data from the BMI270/BMM150 IMU on the Arduino Nano 33 BLE Sense
   It streams X, Y, Z acceleration values along with a labeled activity over 
   serial in CSV format for ML data collection
*/

#include <Arduino_BMI270_BMM150.h>   // Include the library for the BMI270/BMM150 IMU

#define SAMPLE_DELAY 20              // Sampling delay in milliseconds (~50 Hz)

String currentLabel = "walking";     // Label for the activity being recorded

void setup() {
  Serial.begin(115200);              // Initialize serial communication at 115200 baud
  if (!IMU.begin()) {                // Initialize the IMU sensor
    while (1);                       // If IMU fails to initialize, stay in an infinite loop
  }
  Serial.println("ax,ay,az,label");  // Print CSV header to identify columns
}

void loop() {
  float ax, ay, az;                  // Variables to store accelerometer readings

  if (IMU.accelerationAvailable()) {  // Check if new accelerometer data is available
    IMU.readAcceleration(ax, ay, az); // Read acceleration data into ax, ay, az
    Serial.print(ax, 4);              // Print X-axis acceleration with 4 decimal places
    Serial.print(",");                // Separate columns with commas
    Serial.print(ay, 4);              // Print Y-axis acceleration
    Serial.print(",");                // Column separator
    Serial.print(az, 4);              // Print Z-axis acceleration
    Serial.print(",");                // Column separator
    Serial.println(currentLabel);     // Print the activity label and move to next line
    delay(SAMPLE_DELAY);              // Wait before taking the next sample
  }
}
