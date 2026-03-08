# Joshua Geoghegan
# 3/8/2026

# This script collects data from the Arduino via serial communication and 
# saves it to a CSV file with a label for each recording session.
# It allows you to specify the type of motion idle, swing, impact 
# and will automatically generate a filename based on the label and timestamp. 
# The script also prints out progress updates and a summary of the recording session.



import serial # For serial communication with Arduino
import csv # For writing data to CSV files
import time # For timing the recording session

# Configuration
port = "COM4"       # Arduino serial port
baud = 115200
duration = 10       # seconds to record

# Label: 0=idle, 1=swing, 2=impact
label = 0  # Change for each recording session
label_names = {0: 'idle', 1: 'swing', 2: 'impact'}

# Create filename with label and timestamp
import datetime

# Generate filename with label and timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{label_names[label]}_{timestamp}.csv"

# Connect to Arduino
ser = serial.Serial(port, baud, timeout=1)
time.sleep(2)  # Give Arduino time to reset

# Start recording
print(f"Recording {label_names[label]} data for {duration} seconds...") # Added label name to print statement
print(f"Saving to: {filename}")    # Added filename to print statement
print("Press Ctrl+C to stop early") # Added instruction for stopping early
print("-" * 50) # Added separator for readability

# Initialize recording variables
start_time = time.time() 
sample_count = 0

try: # Open CSV file for writing
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f) # Write header with label
        writer.writerow(["ax","ay","az","gx","gy","gz","label"])  # Added label column

        print("Recording...")

        # Read data from serial and write to CSV
        while time.time() - start_time < duration:
            line = ser.readline().decode().strip() # Read line from serial
            
            # Expecting 6 comma separated values: ax, ay, az, gx, gy, gz
            if line:
                data = line.split(",")
                # Only write if we have exactly 6 values
                if len(data) == 6:  # Arduino sending 6 values
                    # Add the label
                    data.append(str(label))
                    writer.writerow(data)
                    
                    # Increment sample count
                    sample_count += 1
                    
                    # Show progress every second
                    if sample_count % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = sample_count / elapsed
                        print(f"  {sample_count} samples ({rate:.1f} Hz)")
# Handle Ctrl+C to stop recording
except KeyboardInterrupt:
    print("\nStopped early by user")
# Handle any other exceptions
finally:
    ser.close()
    # Calculate actual duration and rate
    actual_duration = time.time() - start_time
    actual_rate = sample_count / actual_duration
    
    # Print summary of recording session
    print("-" * 50)
    print(f"Recording finished")
    print(f"Collected: {sample_count} samples in {actual_duration:.1f} seconds")
    print(f"Actual rate: {actual_rate:.1f} Hz") 
    print(f"Saved to: {filename}")