/*
Joshua Geoghegan
JG20251202
TU816, B.Eng Computer Engineering
Stage 4
Project
Suprvisor: Mark Deegan

Code to test sending a random value, pieve of data, tyo FireBase
Firebase is the database
That I have set up for testing software steps as part of my 4th Year project

*/

// Need these to use the WiFi functions
#include <WiFi.h>
// to send and receive data over the internet, we are going to use this for communication with FireBase
#include <HTTPClient.h>
// Converting something to JSON before sending, because firebase likes to receive (and return ) JSON
#include <ArduinoJson.h>

const char* ssid = "DESKTOP-LPIC61A";
const char* password = "12345678";

// This is a single, hard-coded URL for the later http request. We might split it into parts.
const char* firebaseURL = "https://firestore.googleapis.com/v1/projects/smart-hurley-test/databases/(default)/documents/test_data?key=AIzaSyDp1ep5j_90oInc9v2YJf1RKNG2cHG13WE";
const char* theURL =        "https://firestore.googleapis.com";
const char* theInstance =   "/v1/projects/smart-hurley-test/databases/(default)/documents/test_data";
const char* theAPIKey =     "?key=AIzaSyDp1ep5j_90oInc9v2YJf1RKNG2cHG13WE";
// this is not very pretty, but it should; work
// then we use 'theFullFirebaseURL' instead of 'firebaseURL'
const char* partial1 = strcat(theURL, theInstance);
const char* theFullFirebaseURL = strcat(partial1, theAPKey);

/* Question:
What is the capabilityt of the firebase instance? 
Is it a full database? 
Could we be setting up tables and relationships between tables in firebase ?
Could we be defining functions or routines directly in the Database?
*/

////////// ////////// ////////// //////////
// The usual setup function as found in all Arduibno sketches.
void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
} // end of the setup function
////////// ////////// ////////// //////////

////////// ////////// ////////// //////////
void loop() {
  // how about some comments, for a start?
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

 } // end of the loo function
////////// ////////// ////////// //////////
