/*
Joshua Geoghegan

This code reads acceleration from the Nano 33 BLE Sense Rev2 and calculates the overall movement. 
It smooths the data with a moving average and uses thresholds to classify the 
activity as stationary, walking, or running. The result is printed in real time to the serial monitor.

*/
#include <Arduino_BMI270_BMM150.h>  //Library for Nano 33 BLE Sense IMU

//Moving average filter setup
const int WINDOW_SIZE = 10;        //Number of samples for moving average
float accelWindow[WINDOW_SIZE];    //Array to store recent acceleration magnitudes
int winIndex = 0;                  //Current position in the moving average window
float sum = 0;                     //Sum of values in the window for averaging

//Movement detection thresholds (in g)
const float WALK_THRESHOLD = 1.05;   //Filtered magnitude above this = walking
const float RUN_THRESHOLD  = 1.25;   //Filtered magnitude above this = running

void setup() {
  Serial.begin(9600);                //Start serial monitor

  //Initialize BMI270 IMU
  if (!IMU.begin()) {                 //Begin communication with the onboard IMU
    Serial.println("BMI270 IMU init failed!"); //Error message if IMU fails
    while (1);                        //Stop program if IMU not found
  }

  Serial.println("BMI270 IMU ready - Activity detection started");
}

void loop() {
  float x, y, z;                      //Variables to hold raw accelerometer data

  if (IMU.accelerationAvailable()) {   //Check if new accelerometer data is ready
    IMU.readAcceleration(x, y, z);     //Read x, y, z acceleration (in g)

    //Compute overall acceleration magnitude
    float magnitude = sqrt(x*x + y*y + z*z);  // sqrt(x^2 + y^2 + z^2)

    //Moving average filter
    sum -= accelWindow[winIndex];      //Subtract the oldest value from sum
    accelWindow[winIndex] = magnitude; //Store the new magnitude in the window
    sum += accelWindow[winIndex];      //Add new value to sum
    winIndex = (winIndex + 1) % WINDOW_SIZE; //Increment window position, wrap around

    float filtered = sum / WINDOW_SIZE; //Compute average smoothed acceleration

    //Simple activity classification
    if (filtered > RUN_THRESHOLD) {          //If filtered magnitude exceeds running threshold
      Serial.println("Running");             //Output running
    } 
    else if (filtered > WALK_THRESHOLD) {    //Else if magnitude exceeds walking threshold
      Serial.println("Walking");             //Output walking
    } 
    else {                                   //Otherwise
      Serial.println("Stationary");          //Output stationary
    }

    delay(20); // Wait 20 ms for ~50 Hz sampling rate
  }
}
