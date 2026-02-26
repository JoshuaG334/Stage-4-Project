//  Joshua Geoghegan
//  2/26/2026

// This program tests the maximum achievable sampling rate from an IMU sensor
// at different serial baud rates. The header comments show test results from
// multiple baud rate configurations.
//----------------------------------
// At 115200 baud rate
//Δt=22376331−22365869 = 10462µs
// 1,000,000 / 10462 = 95.6 Hz
//-----------------------------------
// At 921600 baud rate
// Δt=9028317−9007479 = 20,838 µs
// 1,000,000 / 20838 = 48.0 Hz
//-----------------------------------
// At 250000 baud rate
// 15521304−15510928 = 10376 µs
// 1,000,000 / 10376 = 96.4 Hz
//-----------------------------------
// At 19200 bause rate 
// Δt=23206668−23197005 = 9663 µs
// 1,000,000 / 9663 = 103.5 Hz
//-----------------------------------
// At 9600 baud rate
// Δt=8001921−7992038 = 9883 µs
// 101.2 Hz
//-----------------------------------

// Library for the BMI270
#include <Arduino_BMI270_BMM150.h>

void setup() {
  Serial.begin(9600);   // CHANGE THIS FOR EACH TEST
  while (!Serial);      // Wait for serial port to connect

  // Initialize the IMU sensor
  if (!IMU.begin()) {
    while (1);  // Stop if IMU fails
  }
}

void loop() {
   // Variables to store accelerometer X, Y, Z values
  float ax, ay, az;

  if (IMU.accelerationAvailable()) {

    // Read the latest acceleration values
    IMU.readAcceleration(ax, ay, az);
    // Capture timestamp immediately after reading sensor
    unsigned long t = micros();

    Serial.print(t);
    Serial.print(",");
    Serial.print(ax, 3);// Print with 3 decimal places for readability
    Serial.print(",");
    Serial.print(ay, 3);
    Serial.print(",");
    Serial.println(az, 3); // Add newline at the end
  }
}