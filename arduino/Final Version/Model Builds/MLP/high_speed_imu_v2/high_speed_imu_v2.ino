// Joshua Geoghegan
// Smart Hurley - High Speed IMU v2 - DATA COLLECTION
// Change: removed timestamp from output to reduce bytes per line
// Old line: 123456789,1234,1234,1234,1234,1234,1234  (~35 chars)
// New line: 1234,1234,1234,1234,1234,1234             (~20 chars) = ~40% less data

#include <Arduino_BMI270_BMM150.h>

#define BAUD_RATE    460800
#define SCALE_FACTOR 1000

void setup() {
  Serial.begin(BAUD_RATE);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("ERR:IMU");
    while (1);
  }

  Serial.println("READY");
}

void loop() {
  float ax, ay, az, gx, gy, gz;

  if (!IMU.accelerationAvailable() || !IMU.gyroscopeAvailable()) return;

  IMU.readAcceleration(ax, ay, az);
  IMU.readGyroscope(gx, gy, gz);

  // No timestamp - shorter line = less serial data = higher throughput
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
