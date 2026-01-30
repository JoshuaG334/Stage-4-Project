# Joshua Geoghegan
# 27/01/2026
# data_features.py
# Extracts features from raw accelerometer CSV data for ML training

# Import pandas for data handling CSV reading, DataFrames
import pandas as pd

# Import numpy for numerical operations sqrt, mean
import numpy as np

# Define the window size for feature extraction
# 50 samples = 1 second of data at 50 Hz sampling rate
WINDOW_SIZE = 50  

# Dictionary mapping activity labels to their raw CSV files
RAW_FILES = {
    "walking": "walking.csv",
    "idle": "idle.csv"
}

# Dictionary mapping activity labels to the output feature CSV files
FEATURE_FILES = {
    "walking": "walking_features.csv",
    "idle": "idle_features.csv"
}

# -----------------------------
# Function to extract features from raw accelerometer data
# -----------------------------
def extract_features(df, label):
    # Compute magnitude of acceleration vector for each sample
    # mag = sqrt(ax^2 + ay^2 + az^2)
    df['mag'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)

    # Initialize a list to hold feature dictionaries
    features = []

    # Slide a window of WINDOW_SIZE across the data
    for start in range(0, len(df), WINDOW_SIZE):
        # Select the current window of magnitude values
        window = df['mag'].iloc[start:start+WINDOW_SIZE]

        # Only process full windows
        if len(window) == WINDOW_SIZE:
            # Compute features for this window and append as a dict
            features.append({
                'mean': window.mean(),                       # Average acceleration magnitude
                'std': window.std(),                         # Standard deviation
                'max': window.max(),                         # Maximum value
                'min': window.min(),                         # Minimum value
                'rms': np.sqrt(np.mean(window**2)),          # Root mean square
                'label': label                               # Activity label (walking/idle)
            })

    # Convert list of feature dictionaries into a DataFrame
    return pd.DataFrame(features)

# -----------------------------
# Process each dataset (walking and idle)
# -----------------------------
for label, raw_file in RAW_FILES.items():
    # Read the raw accelerometer CSV for this activity
    df = pd.read_csv(raw_file)

    # Extract features from the raw data
    feature_df = extract_features(df, label)

    # Save the features to a new CSV file
    feature_df.to_csv(FEATURE_FILES[label], index=False)

    # Print confirmation of rows saved
    print(f"{label.capitalize()} features saved: {len(feature_df)} rows")
