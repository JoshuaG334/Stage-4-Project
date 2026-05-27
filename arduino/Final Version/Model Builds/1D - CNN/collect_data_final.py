# Joshua Geoghegan
# Smart Hurley - Final Data Collection Script
# Classes: 0=idle, 1=swing, 2=impact, 3=fake_hit
# Format: timestamp_s, ax, ay, az, gx, gy, gz, label

import serial
import csv
import time
import datetime

# Configuration
PORT        = "COM4"
BAUD        = 460800
DURATION    = 3.0
# We define a SCALE constant to convert the raw integer values from the Arduino into Gs for acceleration and degrees per second for gyroscope.
SCALE       = 1000.0
WRITE_BATCH = 50

LABEL_NAMES = {0: "idle", 1: "swing", 2: "impact", 3: "fake_hit"}

# CHANGE THIS BEFORE EACH RECORDING SESSION
LABEL = 3   # 0=idle  1=swing  2=impact  3=fake_hit

# Filename 
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename  = f"{LABEL_NAMES[LABEL]}_{timestamp}.csv"

# Connect
# We establish a serial connection to the Arduino using the specified PORT and BAUD rate. 
# We set a timeout of 1 second for reading from the serial port and increase the receive buffer size to 
# 65536 bytes to ensure we can handle the incoming data without overflow. After establishing the connection, 
# we wait for 2 seconds to allow the Arduino to reset and then clear any existing data from the input buffer.
print(f"Connecting to {PORT} at {BAUD} baud...")
ser = serial.Serial(PORT, BAUD, timeout=1)
ser.set_buffer_size(rx_size=65536)
time.sleep(2)
ser.reset_input_buffer()

# Wait for READY
# We wait for a "READY" message from the Arduino to ensure that it is ready to receive commands and start sending data. 
# We set a timeout of 5 seconds for this handshake. If the "READY" message is received, we print a confirmation message. 
# If the timeout is reached without receiving "READY",
ready_deadline = time.time() + 5.0
ready = False

# We wait for a "READY" message from the Arduino to ensure that it is ready to receive commands and start sending data. 
# We set a timeout of 5 seconds for this handshake. If the "READY" message is received, we print a confirmation message. 
# If the timeout is reached without receiving "READY", we print a warning message and proceed anyway, while also clearing 
# any existing data from the input buffer to ensure we start with a clean slate for recording.
while time.time() < ready_deadline:
    line = ser.readline().decode(errors="ignore").strip()
    if line == "READY":
        print("Arduino ready!")
        ready = True
        break

# If the timeout is reached without receiving "READY", we print a warning message and proceed anyway, while also clearing 
# any existing data from the input buffer to ensure we start with a clean slate for recording.
if not ready:
    print("READY not received - starting anyway...")
    ser.reset_input_buffer()

# Record
# We print out the label being recorded, the duration of the recording, and the filename where the data will be saved. 
# We then enter a loop that continues until the specified duration has elapsed. Inside the loop, we check for incoming data from the serial port. 
# If data is available, we read it, decode it, and split it into lines. We handle any leftover partial lines from 
# the previous read to ensure we only process complete lines of data. For each complete line, we parse the accelerometer 
# and gyroscope values, convert them to Gs and degrees per second using the SCALE constant, and append them to a batch list along with 
# the timestamp and label. We periodically write batches of data to the CSV file to improve performance. We also print out the number 
# of samples recorded and the effective sampling rate every 200 samples. Finally, we handle keyboard interrupts gracefully to allow stopping 
# the recording early while ensuring that any remaining data in the batch is saved to the file.
print(f"\n{'─'*50}")
print(f"  Label    : {LABEL} = {LABEL_NAMES[LABEL].upper()}")
print(f"  Duration : {DURATION}s")
print(f"  Saving to: {filename}")
print(f"{'─'*50}")

sample_count = 0
start_time   = time.perf_counter()
leftover     = ""
batch        = []

try:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_s", "ax", "ay", "az", "gx", "gy", "gz", "label"])

        print("Recording...")

        # We enter a loop that continues until the specified duration has elapsed. Inside the loop, we check for incoming data from the serial port. 
        # If data is available, we read it, decode it, and split it into lines. We handle any leftover partial lines from the previous read to 
        # ensure we only process complete lines of data
        while time.perf_counter() - start_time < DURATION:
            waiting = ser.in_waiting
            if waiting == 0:
                time.sleep(0.001)
                continue
            
            raw      = ser.read(waiting).decode(errors="ignore")
            combined = leftover + raw
            lines    = combined.split("\n")
            leftover = lines[-1]
            lines    = lines[:-1]
            # For each complete line, we parse the accelerometer and gyroscope values, convert them to Gs and degrees per second using
            # the SCALE constant, and append them to a batch list along with the timestamp and label. We periodically write batches of 
            # data to the CSV file to improve performance.
            for line in lines:
                line = line.strip()
                if not line or line == "READY":
                    continue

                parts = line.split(",")
                if len(parts) != 6:
                    continue
                # We parse the accelerometer and gyroscope values, convert them to Gs and degrees per second using the SCALE 
                # constant, and append them to a batch list along with the timestamp and label. We periodically write batches of data 
                # to the CSV file to improve performance.
                try:
                    ts  = time.perf_counter() - start_time
                    row = [
                        round(ts, 6),
                        int(parts[0]) / SCALE,
                        int(parts[1]) / SCALE,
                        int(parts[2]) / SCALE,
                        int(parts[3]) / SCALE,
                        int(parts[4]) / SCALE,
                        int(parts[5]) / SCALE,
                        LABEL
                    ]
                    # We handle any ValueError exceptions that may occur during the parsing of the sensor data.
                    # If a line cannot be parsed correctly, we simply skip it and continue processing the next line without crashing the program.
                except ValueError:
                    continue
                # We append the parsed and converted data to the batch list, and increment the sample count. If the batch size reaches the defined WRITE_BATCH,
                # we write the batch to the CSV file and clear the batch list. We also print out the number of samples recorded and the 
                # effective sampling rate every 200 samples to provide feedback on the recording progress.
                batch.append(row)
                sample_count += 1

                if len(batch) >= WRITE_BATCH:
                    writer.writerows(batch)
                    batch.clear()

                if sample_count % 200 == 0:
                    elapsed = time.perf_counter() - start_time
                    print(f"  {sample_count} samples @ {sample_count/elapsed:.1f} Hz")
        # After the recording loop finishes, we check if there are any remaining samples in the batch that have not been written to the file. 
        # If so, we write them to ensure that all recorded data is saved properly.
        if batch:
            writer.writerows(batch)

# We handle keyboard interrupts gracefully to allow stopping the recording early while ensuring that any remaining data in the batch is saved to the file.
except KeyboardInterrupt:
    print("\nStopped early by user")
    if batch:
        with open(filename, "a", newline="") as f:
            csv.writer(f).writerows(batch)
# We ensure that the serial connection is closed properly in the finally block, and we calculate and print out the actual duration of 
# the recording, the total number of samples recorded, the effective sampling rate, and the filename where the data was saved for the user's reference.
finally:
    ser.close()
    actual_duration = time.perf_counter() - start_time
    actual_rate     = sample_count / actual_duration if actual_duration > 0 else 0

# We ensure that the serial connection is closed properly in the finally block, and we calculate and print out the actual duration of 
# the recording, the total number of samples recorded, the effective sampling rate, and the filename where the data was saved for the user's reference.
    print(f"{'─'*50}")
    print(f"Done!")
    print(f"Samples  : {sample_count}")
    print(f"Duration : {actual_duration:.1f}s")
    print(f"Avg rate : {actual_rate:.1f} Hz")
    print(f"Saved to : {filename}")
