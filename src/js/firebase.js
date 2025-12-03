// copied from Arduino sketch
    // Generate fake sensor value
    let value = random(0, 100)/1.0;

    // JSON body in Firestore format
    JSONString = toJSONString(value);

    

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

