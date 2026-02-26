/* 
  Joshua Geoghean
  2/26/2026

** this is only instantaneous frequency measured , need to do the average delta **

Determine maximum stable serial transmission rate
using timestamp streaming

current_timestamp - previous_timestamp
fs = 1,000,000 / Δt

EXAMPLe taken from serial monitor
27542565−27542360 = 205 µs
f = 1,000,000 / 205 = 4878 Hz
*/


void setup() {

  // Change baud rate depending on result on python
  // more bytes less baud rat
  Serial.begin(921600);

  while (!Serial);        // Wait for USB
}

void loop() {

  // Read current time in microseconds
  // micros() increments every 1 pico second
  unsigned long t = micros();

  // Transmit timestamp as ASCII integer then a newline = 1 sample
  Serial.println(t);
  //No delay to run as fast as possible
}

