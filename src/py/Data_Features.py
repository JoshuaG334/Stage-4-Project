
#   Joshua Geoghegan
#   1/27/2026
#
#   This script processes accelerometer data from a CSV file
#   and extracts features for machine learning tasks.


import pandas as pd      # Provides data structures (DataFrame) and CSV reading/writing
import numpy as np       # Provides numerical operations (arrays, math functions)

# Load the CSV data
df = pd.read_csv('walking.csv')  
# Reads the accelerometer data recorded from the Arduino
# Columns in CSV: ax, ay, az, label

# Compute acceleration magnitude
df['mag'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
# 'mag' column = sqrt(ax^2 + ay^2 + az^2)
# This gives the overall acceleration magnitude, independent of sensor orientation

# Define window size for feature extraction
window_size = 50  # Number of samples per window (~1 second at 50 Hz)
features = []     # List to store feature dictionaries for each window

# Loop through the data in windows
for start in range(0, len(df), window_size):
    window = df['mag'].iloc[start:start+window_size]  # Get the current window of magnitudes

    # Only process full windows to avoid incomplete data at the end
    if len(window) == window_size:
        # Compute common statistical features for this window
        features.append({
            'mean': window.mean(),                       # Average magnitude
            'std': window.std(),                         # Standard deviation
            'max': window.max(),                         # Maximum value in window
            'min': window.min(),                         # Minimum value in window
            'rms': np.sqrt(np.mean(window**2)),          # Root mean square (signal energy)
            'label': 'walking'                           # Activity label for supervised learning
        })

# Convert features list to a DataFrame
feature_df = pd.DataFrame(features)
# Each row = one window, columns = extracted features + label

# Display the extracted features
print(feature_df)
# Prints a table with mean, std, max, min, rms, and label for each window
