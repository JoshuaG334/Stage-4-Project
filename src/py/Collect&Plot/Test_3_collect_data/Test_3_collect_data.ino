// Joshua Geoghegan
// 3/8/2026

// This code collects accelerometer and gyroscope data from the BMI270 sensor at 100Hz
// It streams the data over the serial port in CSV format
// The data format is: ax,ay,az,gx,gy,gz

// Include the library for the BMI270 accelerometer/gyroscope
#include <Arduino_BMI270_BMM150.h>

// Set sampling rate to 100Hz (100 samples per second)
const int SAMPLING_RATE = 100;
// Calculate the time between samples in milliseconds (1000ms / 100 = 10ms)
const int SAMPLING_INTERVAL_MS = 1000 / SAMPLING_RATE;

void setup() {
  // Start serial communication at 115200 baud
  Serial.begin(115200);
  
  // Wait for serial port to connect
  while (!Serial);
  
  // Initialize the IMU
  if (!IMU.begin()) {
    // If initialization fails print error and stop
    Serial.println("Failed to initialize IMU!");
    while (1);  // Infinite loop to halt the program
  }
}

void loop() {
  // Static variable remembers its value between loop runs
  // This stores the time of the last sample we took
  static unsigned long lastSample = 0;
  
  // Get current time in milliseconds since arduino started
  unsigned long now = millis();
  
  // Check if its time to take another sample
  // current time minus last sample time >= 10ms
  if (now - lastSample >= SAMPLING_INTERVAL_MS) {
    // Update last sample time to now
    lastSample = now;
    
    // Variables to store sensor readings
    float ax, ay, az, gx, gy, gz;
    
    // Check if new accelerometer and gyroscope data is available
    if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
      // Read the accelerometer values ----> in Gs where 1G = 9.8 m/s^2
      IMU.readAcceleration(ax, ay, az);
      
      // Read the gyroscope values in degrees per second
      IMU.readGyroscope(gx, gy, gz);
      
      // Stream the 6 values as CSV (Comma Separated Values)
      // Format: ax,ay,az,gx,gy,gz
      // No labels or text just pure numbers for Python to read
      
      // Print accelerometer X with 3 decimal places
      Serial.print(ax, 3);
      Serial.print(",");  // Comma separator
      
      // Print accelerometer Y with 3 decimal places
      Serial.print(ay, 3);
      Serial.print(",");
      
      // Print accelerometer Z with 3 decimal places
      Serial.print(az, 3);
      Serial.print(",");
      
      // Print gyroscope X with 3 decimal places
      Serial.print(gx, 3);
      Serial.print(",");
      
      // Print gyroscope Y with 3 decimal places
      Serial.print(gy, 3);
      Serial.print(",");
      
      // Print gyroscope Z with 3 decimal places and end the line
      Serial.println(gz, 3);
    }
  }
}