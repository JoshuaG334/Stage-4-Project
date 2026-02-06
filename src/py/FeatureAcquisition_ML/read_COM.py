
import serial  # For serial communication with arduino
import time    # For timing operations and delays
import csv     # For creating and writing to CSV files


SERIAL_PORT = 'COM4'      # Change to aduino's COM port
BAUD_RATE = 115200        # Must match arduino's serial baud rate setting
DURATION = 120            # Record data for 120 seconds
OUTPUT_FILE = 'imu_features_walking.csv'  # Output CSV filename


# Open serial connection to arduino
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
# Wait 2 seconds for arduino to reset and initialize
time.sleep(2)

print("Recording started...")
start_time = time.time()  # Record start time for timing calculations

LABEL = 1  # Activity label: 0 = idle, 1 = walking


# Open CSV file for writing (newline='' prevents extra blank lines)
with open(OUTPUT_FILE, 'w', newline='') as file:
    # Create CSV writer object
    writer = csv.writer(file)
    # Write header row with column names
    writer.writerow(['timestamp', 'mag_mean', 'label'])  # Reduced to only magnitude feature
    
    try:
        # Main recording loop - runs for specified DURATION
        while time.time() - start_time < DURATION:
            # Read a line from serial (arduino output)
            line = ser.readline().decode('utf-8').strip()
            
            # Check if line contains feature data (arduino sends "FEATURE:" prefix)
            if line.startswith("FEATURE:"):
                try:
                    # Extract magnitude mean value by removing "FEATURE:" prefix
                    mag_mean = float(line.replace("FEATURE:", "").strip())
                    
                    # Calculate elapsed time since recording started
                    timestamp = time.time() - start_time
                    
                    # Write data row to CSV file
                    writer.writerow([timestamp, mag_mean, LABEL])
                    
                    # Print to console for real time monitoring
                    print(timestamp, mag_mean, LABEL)
                    
                except ValueError:
                    # Skip lines that can't be converted to float (corrupted data)
                    pass
    
    # Handle user interruption (Ctrl+C)
    except KeyboardInterrupt:
        print("\nRecording manually stopped by user.")
    
    # Always execute cleanup code
    finally:
        ser.close()  # Close serial connection
        print("Recording finished. CSV saved as:", OUTPUT_FILE)