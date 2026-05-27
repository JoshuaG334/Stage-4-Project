/*
Joshua Geoghegan
12/11/2025

This code reads a local text file 'sensorData.txt' and uploads its 
contents to a Firestore database using Firebase Admin SDK.
It authenticates sing a service account key 
Writes the file contents to a document in the 'sensorData' collection.
The document is named 'latest' and contains the file data and a timestamp.

Node.js is used to allow server side javascript to run locally and access local files.
and to interact with Firestore securely
*/

//Load Node.js file system module for reading files
//This allows to read files from local disk
const fs = require('fs');

//Load Firebase Admin SDK
const admin = require('firebase-admin');

//Load your Firebase service account JSON
//Replace with the path to your downloaded key
//Download key is in "project setting" --> service accounts --> generate new private key
const serviceAccount = require("");

//Initialize Firebase Admin with service account credentials
//For Firestore no databaseURL is needed
admin.initializeApp({
  //Authenticate using the service account
  credential: admin.credential.cert(serviceAccount)
});

//Get a reference to the Firestore database
//Object 'db' will be used to interact with Firestore
const db = admin.firestore();

//Read the entire sensorData.txt file as a UTF-8 string
//This will read all lines into one string
const fileContent = fs.readFileSync('sensorData.txt', 'utf8');

//Upload the file contents to Firestore
//Collection: sensorData Document: 'latest'
//Fields: textFileData( this contains full text from file)
//Timestamp adds server timestamp when the upload occurs
db.collection('sensorData').doc('latest').set({
  textFileData: fileContent,
  timestamp: admin.firestore.FieldValue.serverTimestamp()
})
//If the upload is successful log success message
.then(() => console.log('File uploaded successfully!'))
//If there is an error during upload log the error message
.catch((error) => console.error('Error uploading file:', error)); // Error callback
