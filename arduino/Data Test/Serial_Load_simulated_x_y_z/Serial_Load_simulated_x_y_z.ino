/*
  Joshua Geoghegan
  2/26/2026

  Serial load test v2 - TIMESTAMP + 3 VALUES
  Simulates ax, ay, az without reading IMU
  
*/

//** this is only instantaneous frequency measured , need to do the average delta **
// Hz = 1258 
// formula = Current timestamp - previous 
// 16985630−16984835 = 795 micorseconds = t
// f= 1/t = 1/0.000795 = 1258 Hz 
// ---------------------------------------------

void setup() {
  Serial.begin(921600);
  while (!Serial);
}

void loop() {

  unsigned long t = micros();

  // Simulated integer axis values
  int x = 123;
  int y = 456;
  int z = 789;

  // Send CSV formatted line
  Serial.print(t);
  Serial.print(",");
  Serial.print(x);
  Serial.print(",");
  Serial.print(y);
  Serial.print(",");
  Serial.println(z);

}

