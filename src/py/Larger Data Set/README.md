# Accelerometer ML Exercise: Walking vs Idle

**Author:** Joshua Geoghegan  
**Date:** 27/01/2026  

This repository contains Python and Arduino scripts used to record accelerometer data from an Arduino Nano 33 BLE Sense, extract features, and train a simple machine learning classifier to distinguish walking from idle activity. This project serves as a practice exercise to familiarize with edge ML workflows and feature extraction for human activity recognition.



## Repository Contents

| File | Description |
|------|-------------|
| `imu_to_csv.ino` | Arduino sketch that sends accelerometer readings over serial with activity label. |
| `walking_to_csv.py` | Python script to record walking accelerometer data into `walking.csv`. |
| `idle_csv.py` | Python script to record idle accelerometer data into `idle.csv`. |
| `data_features.py` | Extracts statistical features (mean, std, max, min, RMS) from raw CSVs into feature CSVs for ML training. |
| `train_model.py` | Trains and evaluates a K-Nearest Neighbors classifier using the extracted features. |



## How to Use

1. **Record Data**
   - Connect your Arduino Nano 33 BLE Sense to the computer.
   - Upload `imu_to_csv.ino` to the Arduino.
   - Run `walking_to_csv.py` to record walking data.  
   - Run `idle_csv.py` to record idle data.
   - Press **Ctrl+C** to stop recording. Data will be saved in CSV format.

2. **Extract Features**
   - Run `data_features.py`.  
   - This script reads the raw CSVs, calculates magnitude and statistical features in windows (~1 second), and saves them to `walking_features.csv` and `idle_features.csv`.

3. **Train and Evaluate ML Model**
   - Run `train_model.py`.  
   - The script trains a KNN classifier, evaluates it on a test set, and prints the accuracy and confusion matrix.



