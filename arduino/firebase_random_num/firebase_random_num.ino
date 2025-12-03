#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "DESKTOP-LPIC61A";
const char* password = "12345678";

const char* firebaseURL = "https://firestore.googleapis.com/v1/projects/smart-hurley-test/databases/(default)/documents/test_data?key=AIzaSyDp1ep5j_90oInc9v2YJf1RKNG2cHG13WE";

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

    // JSON body in Firestore format
    String body = "{ \"fields\": { \"value\": {\"doubleValue\": " + String(value) + "} } }";

    http.begin(firebaseURL);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(body);
    if(httpResponseCode>0){
      Serial.println("POST success! Value sent: " + String(value));
      Serial.println(http.getString());
    } else {
      Serial.println("Error in POST: " + String(httpResponseCode));
    }
    http.end();
  }

  delay(5000);
}
