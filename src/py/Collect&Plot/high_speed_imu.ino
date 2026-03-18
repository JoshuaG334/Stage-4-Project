// Joshua Geoghegan
// 3/16/2026
// Smart Hurley - High Speed IMU Data Collection

// Integer printing instead of float
// Baud rate 460800
// I2C at 400kHz set in BMI270.cpp
// Waits for BOTH accel+gyro together
// Minimal loop overhead - no millis() throttling, let the sensor ODR drive timing
// Binary-style compact CSV output
//
// Average = 149 Hz
// Label: 0=idle, 1=swing, 2=impact  ← set before flashing

#include <Arduino_BMI270_BMM150.h>

#define BAUD_RATE     460800   // For Nano BLE Sense USB chip
#define SCALE_FACTOR  1000     // Multiply floats by this before casting to int

// Setup
void setup() {
  Serial.begin(BAUD_RATE);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("ERR:IMU"); // Sensor not found, halt
    while (1); // Infinite loop to halt execution
  }

  // Small startup message so python knows arduino is ready
  Serial.println("READY");
}

// Main loop
void loop() {
  float ax, ay, az, gx, gy, gz;

  // Wait until BOTH sensors have fresh data
  // This ensures synchronized readings and minimizes loop overhead
  if (!IMU.accelerationAvailable() || !IMU.gyroscopeAvailable()) return;

  IMU.readAcceleration(ax, ay, az);
  IMU.readGyroscope(gx, gy, gz);

  // Capture timestamp immediately after reading
  unsigned long t = micros();

  // Print as integers - MUCH faster than Serial.print(float, 3)
  // Divide by SCALE_FACTOR in Python to restore: value / 1000.0
  // Format: timestamp,ax,ay,az,gx,gy,gz
  Serial.print(t);
  Serial.print(',');
  Serial.print((int)(ax * SCALE_FACTOR));
  Serial.print(',');
  Serial.print((int)(ay * SCALE_FACTOR));
  Serial.print(',');
  Serial.print((int)(az * SCALE_FACTOR));
  Serial.print(',');
  Serial.print((int)(gx * SCALE_FACTOR));
  Serial.print(',');
  Serial.print((int)(gy * SCALE_FACTOR));
  Serial.print(',');
  Serial.println((int)(gz * SCALE_FACTOR));
}
