#   Joshua Geoghegan
#   1/27/2026
# 
#   This script reads accelerometer data streamed from an arduino Nano 33 BLE sense
#   over serial and saves it directly into a CSV file for later ML processing
#
#   This py code goes along with the arduino code "imu_to_csv.ino"


import serial   # access to serial ports
import time     # delays and timing functions


PORT = 'COM4'        # Change to your Nano port
BAUD = 115200        # Baud rate for nano 33 must match arduino code
FILENAME = 'walking.csv' #  Name of the CSV file where data will be saved

# Open the serial port to start receiving data from the arduino
ser = serial.Serial(PORT, BAUD, timeout=1) # timeout=1 ensures readline() won't hang forever if no data is received

time.sleep(2)  # # Wait 2 seconds to allow the arduino to reset after opening serial

with open(FILENAME, 'w') as f:              # Open the CSV file in write mode ('w')
    print("Recording data to", FILENAME)    # Let the user know recording has started
    f.write("ax,ay,az,label\n")  # Header's

    try:
            # Infinite loop: continuously read data from the serial port
        while True:
            # Read a single line from the serial port, decode bytes to string, and strip newline characters
            line = ser.readline().decode('utf-8').strip()
            if line:
                # If a line was received (not empty), write it to the CSV and print it
                
                f.write(line + "\n") # Write the received line to the CSV file
                print(line)          # Print the received line to the console
    
    # Handle manual stop (Ctrl+C)
    except KeyboardInterrupt:
        print("\nRecording stopped.") # Recording has ended
        ser.close()                   # Close the serial port
