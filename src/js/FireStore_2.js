/*
Joshua Geoghegan
12/12/2025

This script reads the contents of 'sensorData.txt' and uploads it to
Google Firestore using the Firebase Admin SDK
Unlike the previous version which overwrote a single document this version 
uses add() to create a new document every time the script runs
Firestore automatically generates a  unique document ID allowing to keep a full 
historical log of all sensor data uploads
*/

//File system module
const fs = require('fs');
//Firebase Admin SDK
const admin = require('firebase-admin');
//Service account key
const serviceAccount = require("C:\\Users\\joshm\\Documents\\4th year modules\\Project\\smart-hurley-test-firebase-adminsdk-fbsvc-6afeb4bd45.json");

//Initialize Firebase using the service account credentials
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

//Reference to Firestore
const db = admin.firestore();

//Read entire text file into a string
const fileContent = fs.readFileSync('sensorData.txt', 'utf8');

//Create a new document automatically with a generated ID
db.collection('sensorData').add({
  textFileData: fileContent,                       //The file contents
  timestamp: admin.firestore.FieldValue.serverTimestamp() //Server timestamp
})
.then(() => console.log('New document uploaded successfully!')) //Console log success
.catch((error) => console.error('Error uploading file:', error)); //COnsole error
