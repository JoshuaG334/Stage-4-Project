# Joshua Geoghegan
# Smart Hurley - Dataset Builder - MLP
# Key change: impact CSV files only extract windows centred around the
# actual impact peak, not the whole recording. This prevents swing motion
# before/after the strike being labelled as impact and confusing the model.

from pyexpat import features

import pandas as pd
import numpy as np
import glob
import os
from scipy.signal import find_peaks

from signal_analysis import SAMPLE_RATE

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configuration
DATA_FOLDER      = "data"
OUTPUT_FILE      = "model/dataset.csv"
WINDOW_SIZE      = 100     # samples per window 
STEP_SIZE        = 3      # smaller step size = more windows = better model performance but longer training time
IMPACT_THRESHOLD = 8.0    # G - minimum peak to count as a real strike
PEAK_HALF_WIN    = 250     # samples either side of peak to extract windows from

LABEL_MAP = {
    "idle":     0,
    "swing":    1,
    "impact":   2,
    "fake_hit": 3
}
# Create output directory if it doesn't exist
os.makedirs("model", exist_ok=True)

# Feature Extraction
def extract_features(window):
    features = {}   # Dictionary to hold features for this window
    # Calculate magnitude of acceleration and gyroscope signals
    acc_mag  = np.sqrt(window['ax']**2 + window['ay']**2 + window['az']**2)
    gyro_mag = np.sqrt(window['gx']**2 + window['gy']**2 + window['gz']**2)

    # Basic stats for each signal
    for name, signal in [("acc_mag", acc_mag), ("gyro_mag", gyro_mag)]:
        features[f"{name}_mean"] = signal.mean()
        features[f"{name}_std"]  = signal.std()
        features[f"{name}_max"]  = signal.max()
        features[f"{name}_min"]  = signal.min()
        features[f"{name}_rms"]  = np.sqrt((signal**2).mean())

    # Stats for each axis
    for axis in ["ax", "ay", "az"]:
        features[f"{axis}_mean"] = window[axis].mean()
        features[f"{axis}_std"]  = window[axis].std()
    # Stats for gyroscope axes
    for axis in ["gx", "gy", "gz"]:
        features[f"{axis}_mean"] = window[axis].mean()
        features[f"{axis}_std"]  = window[axis].std()

    # Additional features for acceleration magnitude
    features["acc_mag_diff_max"]   = np.max(np.abs(np.diff(acc_mag)))
    
    # Skewness and kurtosis can help capture the shape of the distribution of values in the window, which may 
    # differ between classes (e.g. impact windows may have more extreme values leading to higher skew/kurtosis)
    features["acc_mag_skew"]       = pd.Series(acc_mag).skew()
    features["acc_mag_kurtosis"]   = pd.Series(acc_mag).kurtosis()
    
    # Peak-to-mean and peak-to-std ratios can help capture the prominence of peaks in the signal, which may 
    # be particularly relevant for distinguishing impact windows from others.
    features["acc_peak_to_mean"]   = acc_mag.max() / (acc_mag.mean()  + 1e-6)
    features["acc_peak_to_std"]    = acc_mag.max() / (acc_mag.std()   + 1e-6)
    features["gyro_peak_to_mean"]  = gyro_mag.max() / (gyro_mag.mean() + 1e-6)
    
    # Jerk features (rate of change of acceleration) can help capture sudden changes in motion,
    #  which are likely to occur during impacts.
    jerk = np.abs(np.diff(acc_mag)) * SAMPLE_RATE
    features["jerk_max"]  = jerk.max()
    features["jerk_mean"] = jerk.mean()
    features["jerk_std"]  = jerk.std()

    return features

# Window extraction for non-impact classes (standard sliding window)
def extract_windows_standard(df, label):
    windows = []
    required = ["ax", "ay", "az", "gx", "gy", "gz"]
    df = df[required].dropna()

    # Slide a window across the data with specified step size and extract features, this will confuse 
    # the model for impact windows as they will contain swing motion before/after the strike 
    # which is labelled as impact, but for non-impact classes this is fine as we just want to capture the general motion
    for start in range(0, len(df) - WINDOW_SIZE + 1, STEP_SIZE):
        window   = df.iloc[start:start + WINDOW_SIZE]
        features = extract_features(window)
        features["label"] = label
        windows.append(features)

    return windows

# Window extraction for impact class (peak-centred)
def extract_windows_impact(df, label):
    
    # Only extract windows centred around actual impact peaks.
    # This prevents swing motion before/after the strike being
    # labelled as impact and confusing the model.
    
    windows  = []
    required = ["ax", "ay", "az", "gx", "gy", "gz"]
    df       = df[required].dropna().reset_index(drop=True)

    acc_mag = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2).values

    # Find peaks above threshold
    peaks, _ = find_peaks(
        acc_mag,
        height=IMPACT_THRESHOLD,
        distance=50  # minimum 50 samples between peaks
    )

    if len(peaks) == 0:
        # No peaks found above threshold fall back to standard windowing
        # but flag it so we can see in output
        return extract_windows_standard(df, label), True

    for peak_idx in peaks:
        # Extract a region centred on the peak
        region_start = max(0, peak_idx - PEAK_HALF_WIN)
        region_end   = min(len(df), peak_idx + PEAK_HALF_WIN)
        region       = df.iloc[region_start:region_end]

        # Slide windows within this peak region only
        for start in range(0, len(region) - WINDOW_SIZE + 1, STEP_SIZE):
            window   = region.iloc[start:start + WINDOW_SIZE]
            if len(window) < WINDOW_SIZE:
                continue
            features = extract_features(window)
            features["label"] = label
            windows.append(features)

    return windows, False

# Main
all_windows = []
csv_files   = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
fallback_count = 0
# Print summary of found files and labels
print(f"Found {len(csv_files)} CSV files in '{DATA_FOLDER}'\n")
# Process each file
for filepath in csv_files:
    filename = os.path.basename(filepath)
    # Determine label from filename prefix
    label = None
    for key in LABEL_MAP:
        if filename.lower().startswith(key):
            label      = LABEL_MAP[key]
            label_name = key
            break
    # If no label found, skip this file with a warning
    if label is None:
        print(f"  [SKIP] {filename} - no matching label prefix")
        continue
    # If label found, process the file
    df = pd.read_csv(filepath)
    # Check required columns are present
    required = ["ax", "ay", "az", "gx", "gy", "gz"]
    if not all(col in df.columns for col in required):
        print(f"  [SKIP] {filename} - missing columns")
        continue
    # Extract windows using appropriate method for this label
    # For impact files, use peak-centred extraction. If no peaks above threshold are found, fall back to standard windowing 
    # but count it so we can see in output.
    if label == LABEL_MAP["impact"]:
        windows, fallback = extract_windows_impact(df, label)
        if fallback:
            fallback_count += 1
            print(f"  [WARN] {filename:45s} → no peak above {IMPACT_THRESHOLD}G, used standard windowing")
        else:
            print(f"  [OK]  {filename:45s} → impact (peak-centred) {len(windows)} windows")
    else:
        windows = extract_windows_standard(df, label)
        print(f"  [OK]  {filename:45s} → {label_name:10s} {len(windows)} windows")
    # Add extracted windows to the overall dataset
    all_windows.extend(windows)
# After processing all files, create a DataFrame and save to CSV
dataset = pd.DataFrame(all_windows)
dataset.to_csv(OUTPUT_FILE, index=False)

# Print final summary
print(f"\n{'─'*55}")
print(f"Total windows : {len(dataset)}")
if fallback_count > 0:
    print(f"Fallback files: {fallback_count} impact files had no peak above {IMPACT_THRESHOLD}G")
    print(f"  → Consider lowering IMPACT_THRESHOLD if too many fallbacks")
print(f"\nClass breakdown:")
for name, idx in LABEL_MAP.items():
    count = (dataset['label'] == idx).sum()
    bar   = "█" * (count // 10)
    print(f"  {name:10s} ({idx}): {count:5d} windows  {bar}")
print(f"\nSaved to: {OUTPUT_FILE}")
print("Next: run 2_train_model_final.py")