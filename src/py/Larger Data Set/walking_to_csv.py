# Joshua Geoghegan
# 27/01/2026
# serial_to_csv.py
# Records WALKING accelerometer data from Arduino and appends to walking.csv

# Import serial module to communicate with Arduino over USB
import serial

# Import time for sleep delays
import time

# Import os to check if file exists
import os

# -----------------------------
# Configuration
# -----------------------------
PORT = "COM4"        # Serial port of arduino
BAUD = 115200        # Baud rate for serial communication
FILENAME = "walking.csv"  # CSV file to save the recorded walking data

# Initialize serial connection to arduino
ser = serial.Serial(PORT, BAUD, timeout=1)

# Small delay to allow arduino to reset and start sending data
time.sleep(2)  

# Check if the CSV file already exists
file_exists = os.path.isfile(FILENAME)

# Open the CSV file in append mode
with open(FILENAME, "a") as f:
    
    # If file does not exist, write the CSV header
    if not file_exists:
        f.write("ax,ay,az,label\n")  # Columns: X, Y, Z accelerations + label

    # Inform the user that recording has started
    print("Recording WALKING data... Press Ctrl+C to stop.")

    try:
        # Infinite loop to read data from arduino
        while True:
            # Read one line from serial decode to string strip newline/whitespace
            line = ser.readline().decode("utf-8").strip()
            
            # Only process non empty lines
            if line:
                # Write line to CSV
                f.write(line + "\n")
                
                # Print line to console for monitoring
                print(line)
                
    # Handle Ctrl+C to safely stop recording
    except KeyboardInterrupt:
        print("\nWalking data recording stopped.")
        ser.close()  # Close serial connection
