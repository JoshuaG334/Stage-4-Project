// Joshua Geoghegan
// 2/26/2026

//This program reads and outputs data from BOTH the accelerometer and gyroscope
// simultaneously. The header shows a measured sampling rate of 67.4 Hz when
// both sensors are enabled.
//---------------------------------
// at 115200 baud
// Δt=15810673−15795836 = 14,837 µs
// 67.4 Hz
//--------------------------------
// at 921600 baud
// Δt=44813779−44797512 = 16,267 µs
// 61.5 Hz

// Library for BMI270
#include <Arduino_BMI270_BMM150.h>

void setup() {
  Serial.begin(921600); // Initialize serial communication at 115200 baud
  while (!Serial);      // Wait for serial port to connect 

  // Initialize the IMU sensor
  if (!IMU.begin()) {
    while (1); // enter infinite loop to prevent garbage data output if no init
  }
}

void loop() {
  // Variables for accelerometer data
  float ax, ay, az;
  // Variables for gyroscope data
  float gx, gy, gz;

  // Check if both accelerometer AND gyroscope have new data available
  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
    
    // Read accelerometer & gyroscope values
    IMU.readAcceleration(ax, ay, az);
    IMU.readGyroscope(gx, gy, gz);

    // Capture precise timestamp immediately after reading both sensors
    unsigned long t = micros();

    // Output data in CSV format with 7 columns
    // Accelerometer data
    Serial.print(t);
    Serial.print(",");
    Serial.print(ax, 3);
    Serial.print(",");
    Serial.print(ay, 3);
    Serial.print(",");
    Serial.print(az, 3);

    // Gyroscope data
    Serial.print(",");
    Serial.print(gx, 3);
    Serial.print(",");
    Serial.print(gy, 3);
    Serial.print(",");
    Serial.println(gz, 3);
  }
}