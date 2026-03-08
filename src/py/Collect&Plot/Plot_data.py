# Joshua Geoghegan
# 3/8/2026

# This script allows you to select a CSV file containing accelerometer and gyroscope data,
# and then plots the data while also printing out some statistics about the recorded motion.
# It is useful for visualizing the raw data collected from the Arduino

import pandas as pd # For data manipulation
import matplotlib.pyplot as plt # For plotting
import glob # For file handling
import numpy as np # For numerical operations

# Show all CSV files in current folder
csv_files = glob.glob("*.csv")
print("Available CSV files:")
for i, file in enumerate(csv_files): # Print index and filename
    print(f"{i}: {file}") # Show index and filename for selection

# Pick by number
choice = int(input("\nEnter file number: "))
filename = csv_files[choice] # Get the filename based on choice

print(f"\nLoading {filename}...") # Load the selected CSV file into a DataFrame
df = pd.read_csv(filename)

# Calculate stats
acc_mag = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
gyro_mag = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2)

print(f"\n=== STATISTICS ===")
print(f"Total samples: {len(df)}") # Print total number of samples
print(f"\nACCELERATION (G):") # Print max acceleration and max rate of change
print(f"Max X: {df['ax'].max():.3f}") # Print max ax value
print(f"Max Y: {df['ay'].max():.3f}") # Print max ay value
print(f"Max Z: {df['az'].max():.3f}") # Print max az value
print(f"Max Magnitude: {acc_mag.max():.3f}G") # Print max magnitude of acceleration
print(f"Mean Magnitude: {acc_mag.mean():.3f}G") # Print mean magnitude of acceleration
print(f"\nGYROSCOPE (dps):") # Print max gyroscope values
print(f"Max X: {df['gx'].max():.1f}") # Print max gx value
print(f"Max Y: {df['gy'].max():.1f}") # Print max gy value
print(f"Max Z: {df['gz'].max():.1f}") # Print max gz value
print(f"Max Magnitude: {gyro_mag.max():.1f} dps") # Print max magnitude of gyroscope
print(f"Mean Magnitude: {gyro_mag.mean():.1f} dps") # Print mean magnitude of gyroscope
print(f"\nRATE OF CHANGE:") # Print max rate of change of acceleration magnitude
print(f"Max Rate: {np.max(np.abs(np.diff(acc_mag))):.3f} G/sample") # Print max rate of change of acceleration magnitude

# Create plots
fig, axes = plt.subplots(2, 1, figsize=(12, 8)) # Create 2 subplots for accelerometer and gyroscope
fig.suptitle(f'File: {filename} - Label: {df["label"].iloc[0]}', fontsize=14) # Add title with filename and label

# Plot 1: Accelerometer
axes[0].plot(df['ax'], label='ax', alpha=0.7) # Plot ax with label and some transparency
axes[0].plot(df['ay'], label='ay', alpha=0.7) # Plot ay with label and some transparency
axes[0].plot(df['az'], label='az', alpha=0.7) # Plot az with label and some transparency
axes[0].set_ylabel('Acceleration (G)') # Set y axis label for accelerometer
axes[0].set_title('Accelerometer') # Set title for accelerometer plot
axes[0].legend() # Show legend for accelerometer plot
axes[0].grid(True, alpha=0.3) # Add grid to accelerometer plot with some transparency

# Plot 2: Gyroscope
axes[1].plot(df['gx'], label='gx', alpha=0.7)
axes[1].plot(df['gy'], label='gy', alpha=0.7)
axes[1].plot(df['gz'], label='gz', alpha=0.7)
axes[1].set_ylabel('Gyroscope (dps)') # Set y axis label for gyroscope
axes[1].set_xlabel('Sample Number') # Set x axis label for gyroscope
axes[1].set_title('Gyroscope') # Set title for gyroscope plot
axes[1].legend() # Show legend for gyroscope plot
axes[1].grid(True, alpha=0.3) # Add grid to gyroscope plot with some transparency

plt.tight_layout() # Adjust layout to prevent overlap
plt.show() # Show the plots