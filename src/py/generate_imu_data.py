# Joshua Geoghegan 
# 12/15/2025

# This script generates synthetic IMU data (accelerometer and gyroscope)
# and saves it to a text file named "imu_data_raw.txt"

#Import the random module to generate synthetic data
import random

fs = 50          #Sampling frequency (Hz)
dt = 1 / fs      #Sampling interval (s)

#Number of samples to generate
#500 samples at 50 Hz = 10 seconds of data
samples = 500

#Open OR create the file imu_data_raw.txt in write mode
with open("imu_data_raw.txt", "w") as f:
    t = 0.0       #Initialize time variable  = timestamp
    #Loop over the number of samples to generate
    for _ in range(samples):

        #Generate synthetic accelerometer data x-axis,y-axis, z-axis 
        # ax, ay, az) in m/s^2
        #Small random variation around 0 simulate "noise"
        ax = round(random.uniform(-0.2, 0.2), 2)
        ay = round(random.uniform(-1.5, -0.8), 2)
        az = round(random.uniform(9.5, 9.9), 2)

        #Generate synthetic gyroscope data (gx, gy, gz) in deg/s
        gx = round(random.uniform(-2.0, 2.0), 2)
        gy = round(random.uniform(-2.0, 2.0), 2)
        gz = round(random.uniform(-1.0, 1.0), 2)

        #Write the timestamp and IMU data to the file
        #Format: time(s), ax, ay, az, gx, gy, gz
        #Each value separated by a comma easier for parsing later
        f.write(f"{t:.3f}, {ax}, {ay}, {az}, {gx}, {gy}, {gz}\n")
        #Increment time by the sampling interval
        #ensure a fixed sampling rate 50 hz
        t += dt
