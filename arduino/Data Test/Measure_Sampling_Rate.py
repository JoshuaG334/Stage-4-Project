# Joshua Geoghegan
# 2/26/26

# This script reads timestamps from a serial port and checks for any jumps in the timestamps 
# that exceed a specified threshold. If a jump is detected it indicates that the stream is unstable. 
# otherwise it indicates that the stream is stable.

import serial # serial library for serial communication
import time   # time library for sleep function

# Open the serial port with the specified port, baud rate, and timeout same as the Arduino code
ser = serial.Serial('COM4', 921600, timeout=1)
time.sleep(2)   # wait for the serial connection to initialize


previous = None # variable to store the previous timestamp
jump_detected = False # flag to indicate if a timestamp jump is detected

THRESHOLD = 1000  # microseconds

for i in range(1000):  # read 1000 samples
    line = ser.readline().decode().strip() # read a line from the serial port decode it to string and strip whitespace
    
    # Check if the line is a digit timestamp and process it
    if line.isdigit():
        current = int(line) # convert the timestamp to an integer
        
        if previous is not None: # if we have a previous timestamp, calculate the difference
            delta = current - previous # calculate the difference between current and previous timestamp
            if delta > THRESHOLD:      # if the difference exceeds the threshold, we consider it a jump
                jump_detected = True   # set the flag to indicate a jump is detected
                break                  # exit the loop if a jump is detected
        
        previous = current              # update the previous timestamp to the current one

ser.close() # close the serial port

# Print the result based on whether a jump was detected or not
if jump_detected:
    print("YES - Timestamp jump detected (unstable)")
else:
    print("NO - Stream stable")

    