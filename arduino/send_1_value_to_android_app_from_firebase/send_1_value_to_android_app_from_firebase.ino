#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "";
const char* password = "";

<<<<<<< Updated upstream
const char* firebaseURL = "";
=======
const char* firebaseURL = "*******";
>>>>>>> Stashed changes

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
}

void loop() {
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;

    // Generate fake sensor value
    float value = random(0, 100)/1.0;

    // Get current time in ISO 8601 format (RFC3339)
    // For testing, just use millis() and convert to seconds
    unsigned long t = millis()/1000;
    String timestamp = "2025-12-01T00:00:00Z"; // You can replace with real timestamp if you have RTC

    // JSON body in Firestore format with timestamp
    String body = "{ \"fields\": { "
                  "\"value\": {\"doubleValue\": " + String(value) + "},"
                  "\"timestamp\": {\"timestampValue\": \"" + timestamp + "\"}"
                  "} }";

    http.begin(firebaseURL);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(body);
    if(httpResponseCode>0){
      Serial.println("POST success! Value sent: " + String(value));
    } else {
      Serial.println("Error in POST: " + String(httpResponseCode));
    }
    http.end();
  }

  delay(30000);
}
