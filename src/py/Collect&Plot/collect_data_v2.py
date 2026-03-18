# Joshua Geoghegan
# Smart Hurley - High Speed Data Collection
# No longer gets stuck waiting for READY
# uses a timeout fallback - if READY not received in 5s, starts anyway
# also flushes the buffer before recording to clear any startup garbage

import serial
import csv
import time
import datetime

# Configuration
PORT        = "COM4"
BAUD        = 460800
DURATION    = 10
SCALE       = 1000.0
# Label for the data being collected - change this for each type of motion you want to record
LABEL       = 0
LABEL_NAMES = {0: "idle", 1: "swing", 2: "impact"}
WRITE_BATCH = 50

# Filename 
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename  = f"{LABEL_NAMES[LABEL]}_{timestamp}.csv"

# Connect to serial port
print(f"Connecting to {PORT} at {BAUD} baud...")
ser = serial.Serial(PORT, BAUD, timeout=1)
ser.set_buffer_size(rx_size=65536)
time.sleep(2)

# Flush anything in the buffer from startup
ser.reset_input_buffer()

# Wait for ready but don't get stuck - timeout after 5 seconds and start anyway
print("Waiting for Arduino (timeout 5s)...")
ready_deadline = time.time() + 5.0
ready = False


while time.time() < ready_deadline:
    line = ser.readline().decode(errors="ignore").strip()
    if line == "READY":
        print("Arduino ready!")
        ready = True
        break

if not ready:
    print("READY not received - starting anyway...")
    ser.reset_input_buffer()  # flush any garbage before recording

# Record
print(f"\nRecording [{LABEL_NAMES[LABEL]}] for {DURATION}s -> {filename}")
print("Press Ctrl+C to stop early")
print("-" * 50)

sample_count = 0
start_time   = time.perf_counter()
leftover     = ""
batch        = []

# Open CSV file and write header, then loop reading from serial and writing to file in batches.
# The Arduino sends lines of comma separated values with ax, ay, az, gx, gy, gz. We parse these,
try:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_s", "ax", "ay", "az", "gx", "gy", "gz", "label"])

        print("Recording...")

        while time.perf_counter() - start_time < DURATION:

            waiting = ser.in_waiting
            if waiting == 0:
                time.sleep(0.001)
                continue
            # Read all available data, split into lines, and keep any incomplete line for the next batch
            raw      = ser.read(waiting).decode(errors="ignore")
            combined = leftover + raw
            lines    = combined.split("\n")
            leftover = lines[-1]
            lines    = lines[:-1]
            # Process each complete line
            for line in lines:
                line = line.strip()
                if not line or line == "READY":
                    continue
                # Each line should have 6 comma-separated values: ax, ay, az, gx, gy, gz (scaled by 1000 and sent as integers)
                parts = line.split(",")
                if len(parts) != 6:
                    continue
                # Parse the values, convert to floats by dividing by SCALE, and add a timestamp. If parsing fails, skip the line.
                try:
                    ts = time.perf_counter() - start_time
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
                except ValueError: # If conversion fails, skip this line
                    continue
                
                # Add the parsed row to the batch. When the batch reaches WRITE_BATCH size, 
                # write it to the CSV file and clear the batch.
                batch.append(row)
                sample_count += 1
                # Write in batches to reduce file I/O overhead
                if len(batch) >= WRITE_BATCH:
                    writer.writerows(batch)
                    batch.clear()
                # Print progress every 200 samples with current rate in Hz
                if sample_count % 200 == 0:
                    elapsed = time.perf_counter() - start_time
                    print(f"  {sample_count} samples @ {sample_count/elapsed:.1f} Hz")
        # Write any remaining samples in the batch after recording is done  
        if batch:
            writer.writerows(batch)
# Handle Ctrl+C gracefully to allow early stopping and ensure file is saved
except KeyboardInterrupt:
    print("\nStopped early by user")
    if batch:
        with open(filename, "a", newline="") as f:
            csv.writer(f).writerows(batch)
# Make sure to close the serial port and print final stats even if an error occurs
finally:
    ser.close()
    actual_duration = time.perf_counter() - start_time
    actual_rate     = sample_count / actual_duration if actual_duration > 0 else 0
    # Print final stats
    print("-" * 50)
    print(f"Done!")
    print(f"Samples  : {sample_count}")
    print(f"Duration : {actual_duration:.1f}s")
    print(f"Avg rate : {actual_rate:.1f} Hz")
    print(f"Saved to : {filename}")