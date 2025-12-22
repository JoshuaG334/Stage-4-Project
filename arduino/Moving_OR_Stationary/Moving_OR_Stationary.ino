/*
Joshua Geoghegan
12/22/2025

This code reads accelerometer data from the Nano 33 BLE Sense Rev2 and calculates the overall acceleration. 
It smooths the data using a moving average filter to reduce noise.
Based on the filtered values it detects whether the device is stationary or in motion and prints the result to the serial monitor.
*/

#include <Arduino_BMI270_BMM150.h>  //Include the library for Nano 33 BLE Sense IMU

//Moving average filter setup
const int WINDOW_SIZE = 10;        //Number of samples to average smoothing window
float accelWindow[WINDOW_SIZE];    //Array to store recent acceleration magnitudes
int winIndex = 0;                  //Index to track current position in the moving average window
float sum = 0;                     //Sum of values in the moving average window

//Movement detection threshold
const float MOVEMENT_THRESHOLD = 1.05;  //Acceleration magnitude (in g) above which movement is detected

void setup() {
  Serial.begin(9600);                //Start the serial monitor at 9600 baud

  //Initialize BMI270 IMU
  if (!IMU.begin()) {                 //Try to initialize the IMU
    Serial.println("BMI270 IMU init failed!"); //If initialization fails print error
    while (1);                        //Stop program if IMU not found
  }

  Serial.println("BMI270 IMU ready - Movement detection started"); //Confirm IMU is ready
}

void loop() {
  //Variables to hold raw accelerometer data from x, y, z axes
  float x, y, z;

  //Check if new accelerometer data is available
  if (IMU.accelerationAvailable()) {
    //Read accelerometer values (in g)
    IMU.readAcceleration(x, y, z);

    //Compute acceleration magnitude

    //Calculate the overall acceleration magnitude
    float magnitude = sqrt(x*x + y*y + z*z);

    //Moving average filter
    sum -= accelWindow[winIndex];      //Subtract the oldest value from the sum
    accelWindow[winIndex] = magnitude; //Store the new magnitude in the array
    sum += accelWindow[winIndex];      //Add the new value to the sum
    winIndex = (winIndex + 1) % WINDOW_SIZE; //Increment index and wrap around if needed

    float filtered = sum / WINDOW_SIZE; //Calculate the average smoothed acceleration

    //Movement detection
    if (filtered > MOVEMENT_THRESHOLD) {  //If filtered value exceeds threshold
      Serial.println("Movement detected!"); //Print movement detected
    } 
    else {                                 //Otherwise
      Serial.println("Stationary");        //Print stationary
    }

    delay(20); //Wait 20 ms to get ~50 Hz sampling rate
  }
}
