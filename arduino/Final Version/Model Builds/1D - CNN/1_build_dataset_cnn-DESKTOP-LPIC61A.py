# Joshua Geoghegan
# Smart Hurley - 1D CNN Dataset Builder
# Unlike the feature-based approach, this script keeps the RAW signal
# values from each window rather than computing summary statistics.
# The CNN learns its own features directly from the waveform shape.
#
# Output shape: (num_windows, WINDOW_SIZE, 6)
# 6 channels: ax, ay, az, gx, gy, gz

import pandas as pd
import numpy as np
import glob
import os
from scipy.signal import find_peaks

# Configuration 
DATA_FOLDER      = "../testing/data"   # same data folder as feature-based approach
OUTPUT_X         = "model/X_raw.npy"   # raw windows array
OUTPUT_Y         = "model/y_raw.npy"   # labels array
WINDOW_SIZE      = 100                  # samples per window - same as feature-based
STEP_SIZE        = 3                   # sliding window step
IMPACT_THRESHOLD = 8.0                 # G - minimum peak for impact windowing
PEAK_HALF_WIN    = 250                 # samples either side of peak

# label mapping - same as feature-based approach for consistency
LABEL_MAP = {
    "idle":     0,
    "swing":    1,
    "impact":   2,
    "fake_hit": 3
}
# For reporting purposes
LABEL_NAMES = {0: "idle", 1: "swing", 2: "impact", 3: "fake_hit"}
# The 6 channels we care about - same as feature-based approach for consistency
CHANNELS = ["ax", "ay", "az", "gx", "gy", "gz"]

# Ensure output directory exists
os.makedirs("model", exist_ok=True)

# Standard sliding window (non-impact classes)
def extract_windows_standard(df, label):
    # Drop rows with missing values in the relevant channels, then create windows
    windows = []
    # We dropna() here to ensure we only create windows from complete data. 
    # If there are missing values, those rows will be skipped, which may reduce the number of windows but ensures data quality.
    df = df[CHANNELS].dropna()
    # We reset the index after dropping rows to ensure our window slicing works correctly.
    for start in range(0, len(df) - WINDOW_SIZE + 1, STEP_SIZE):
        # We take a slice of the dataframe for the current window. The .values attribute converts it to a NumPy array of shape (WINDOW_SIZE, 6).
        window = df.iloc[start:start + WINDOW_SIZE].values  # shape (50, 6)
        # We check if the window has the correct number of samples. If the last window is shorter than WINDOW_SIZE, we skip it.
        windows.append((window, label))
    return windows

# Peak-centred window extraction (impact class)
def extract_windows_impact(df, label):
    # We calculate the magnitude of the acceleration vector to find peaks that indicate impacts.
    windows = []
    # We dropna() here to ensure we only calculate peaks from complete data. 
    # If there are missing values, those rows will be skipped, which may reduce the number of peaks found but ensures data quality.
    df = df[CHANNELS].dropna().reset_index(drop=True)
    # The magnitude of the acceleration is calculated using the formula: sqrt(ax^2 + ay^2 + az^2). This gives us a single value representing the overall 
    # acceleration at each time step, which is useful for detecting impacts.
    acc_mag = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2).values

    # We use the find_peaks function from scipy.signal to identify peaks in the acceleration magnitude that exceed the IMPACT_THRESHOLD. 
    # The distance parameter ensures that we only consider peaks that are at least 50 samples apart
    peaks, _ = find_peaks(acc_mag, height=IMPACT_THRESHOLD, distance=50)
    
    # If no peaks are found above the threshold, we fall back to standard windowing for this file. 
    # This is a safety measure to ensure we still get some data from files that may not have clear impacts.
    if len(peaks) == 0:
        return extract_windows_standard(df, label), True

    # For each detected peak, we define a region around it (±250 samples) and create windows within that region.
    for peak_idx in peaks:
        # We calculate the start and end indices of the region around the peak, ensuring we don't go out of bounds of the dataframe.
        region_start = max(0, peak_idx - PEAK_HALF_WIN)
        # We calculate the end index of the region, ensuring we don't go beyond the length of the dataframe.
        region_end   = min(len(df), peak_idx + PEAK_HALF_WIN)
        # We take a slice of the dataframe for the current region around the peak. This region is where we expect to find the impact event.
        region       = df.iloc[region_start:region_end]
        # We create windows within this region using the same sliding window approach as the standard method.
        for start in range(0, len(region) - WINDOW_SIZE + 1, STEP_SIZE):
            # We take a slice of the region for the current window. The .values attribute converts it to a NumPy array of shape (WINDOW_SIZE, 6).
            window = region.iloc[start:start + WINDOW_SIZE].values
            # We check if the window has the correct number of samples. If the last window in the region is shorter than WINDOW_SIZE, we skip it.
            if len(window) < WINDOW_SIZE:
                continue
            # We append the window and its corresponding label to the list of windows. Each entry in the windows list is a tuple of (window_data, label).
            windows.append((window, label))

    return windows, False

# Main 
all_X = [] # list to hold all window data
all_y = [] # list to hold corresponding labels

# We use glob to find all CSV files in the specified data folder. This allows us to process each file without hardcoding their names.
csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
# We print the number of CSV files found in the data folder to give feedback on how many files will be processed.
print(f"Found {len(csv_files)} CSV files in '{DATA_FOLDER}'\n")

# We loop through each CSV file, determine its label based on the filename, and extract windows accordingly.
fallback_count = 0

# For each file, we check if its name starts with any of the keys in LABEL_MAP to determine its label. If no matching label is found, we skip the file.
for filepath in csv_files:
    filename = os.path.basename(filepath)
# We initialize the label variable to None. This variable will hold the integer label corresponding to the class of the data in the file (e.g., idle, swing, impact, fake_hit).
    label = None
    for key in LABEL_MAP:
        # We check if the filename starts with the current key (e.g., "idle", "swing", etc.). 
        # If it does, we assign the corresponding label from LABEL_MAP to the label variable and break out of the loop.
        if filename.lower().startswith(key):
            label      = LABEL_MAP[key]
            label_name = key
            break
    # If after checking all keys in LABEL_MAP the label variable is still None, it means the filename did not match any expected class.
    if label is None:
        # We print a warning message indicating that the file is being skipped due to no matching label. This helps us identify any files that may not be named correctly or are not relevant to our dataset.
        print(f"  [SKIP] {filename} - no matching label")
        continue
    # We read the CSV file into a pandas DataFrame. This allows us to easily manipulate and analyze the data.
    df = pd.read_csv(filepath)
    # We check if all the required channels (ax, ay, az, gx, gy, gz) are present in the DataFrame. If any of these columns are missing, we skip the file.
    if not all(col in df.columns for col in CHANNELS):
        # We print a warning message indicating that the file is being skipped due to missing columns. This ensures that we only process files that have the necessary data for our model.
        print(f"  [SKIP] {filename} - missing columns")
        continue

    # Depending on the label, we either extract peak-centred windows for impact files or standard sliding windows for the other classes.
    if label == LABEL_MAP["impact"]:
    # For files labeled as "impact", we call the extract_windows_impact function, 
    # which attempts to find peaks in the acceleration data and create windows around those peaks.
        windows, fallback = extract_windows_impact(df, label)
        if fallback:
            fallback_count += 1
            # If the impact windowing falls back to standard windowing (i.e., no peaks above the threshold were found), we print a warning message indicating this.
            print(f"  [WARN] {filename:45s} → no peak above {IMPACT_THRESHOLD}G, used standard windowing")
        else:
            # If peak-centred windows were successfully extracted, we print a message indicating how many windows were created for this file.
            print(f"  [OK]  {filename:45s} → impact (peak-centred) {len(windows)} windows")
    else:
        # For files that are not labeled as "impact", we call the extract_windows_standard function,
        #  which creates windows using a standard sliding window approach without looking for peaks.
        windows = extract_windows_standard(df, label)
        # We print a message indicating how many windows were created for this file and what label they correspond to.
        print(f"  [OK]  {filename:45s} → {label_name:10s} {len(windows)} windows")

    
    # We loop through the windows extracted from the current file and append the window data and corresponding label to the all_X and all_y lists, respectively.
    for window, lbl in windows:
        # We append the window data (a NumPy array of shape (WINDOW_SIZE, 6)) to the all_X list and the corresponding label (an integer) to the all_y list.
        all_X.append(window)
        # We append the label for this window to the all_y list. This label will be used later when we convert the lists to NumPy arrays and save them to disk.
        all_y.append(lbl)

# Save 
# After processing all files and extracting windows, we convert the all_X and all_y lists into NumPy arrays.
X = np.array(all_X, dtype=np.float32)  # shape: (N, 50, 6)
# We convert the list of window data (all_X) into a NumPy array of type float32. The resulting shape of X will be (N, WINDOW_SIZE, 6), where N is the total number of windows extracted from all files.
y = np.array(all_y, dtype=np.int32)    # shape: (N,)

np.save(OUTPUT_X, X)# We save the X array, which contains the window data, to a .npy file specified by OUTPUT_X. This file can be loaded later for training the CNN model.
np.save(OUTPUT_Y, y)# We save the y array, which contains the corresponding labels for each window, to a .npy file specified by OUTPUT_Y. This file can also be loaded later for training the CNN model.

# Finally, we print a summary of the dataset we have created, including the total number of windows, the shapes of X and y, and a breakdown of how many windows belong to each class. We also indicate where the data has been saved and what the next step is.
print(f"\n{'─'*55}")
print(f"Total windows : {len(X)}")
print(f"X shape       : {X.shape}  (windows, timesteps, channels)")
print(f"y shape       : {y.shape}")
print(f"\nClass breakdown:")
for idx, name in LABEL_NAMES.items():
    count = (y == idx).sum()
    bar   = "█" * (count // 500)
    # We print the class name, its corresponding index, the count of windows for that class 
    # and a simple text-based bar to visually represent the proportion of windows in that class. 
    # The bar length is scaled by dividing the count by 500, so each "█" represents 500 windows.
    print(f"  {name:10s} ({idx}): {count:6d} windows  {bar}")

# We print the total number of windows in the dataset, the shapes of the X and y arrays, and a breakdown of how many windows belong to each class. 
# Finally, we indicate where the processed data has been saved and what the next step is in the workflow
print(f"\nSaved to: {OUTPUT_X}, {OUTPUT_Y}")
print("Next: run 2_train_model_cnn.py")
