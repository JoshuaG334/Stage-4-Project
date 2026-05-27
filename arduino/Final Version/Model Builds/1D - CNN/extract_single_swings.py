# Joshua Geoghegan
# Smart Hurley - Single Swing Extractor
# Takes all swing CSVs from the source data folder, finds each individual
# swing peak, and saves one CSV per swing into the output folder.
#
# Strategy:
#   1. Compute acceleration magnitude for the full CSV
#   2. Find peaks above SWING_THRESHOLD with minimum separation PEAK_MIN_DIST
#   3. For each peak, extract a window of HALF_WIN samples either side
#   4. Save as a new CSV with the same columns and label
#
# Run:
#   python extract_single_swings.py


import os
import glob
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

# Config
SOURCE_FOLDER  = "../ML Final/data"   # where your original CSVs live
OUTPUT_FOLDER  = "data"               # subfolder inside testing/
SWING_THRESHOLD = 2.5                 # minimum peak G to count as a swing
PEAK_MIN_DIST   = 200                 # minimum samples between peaks (~1.6s at 125Hz)
HALF_WIN        = 200                 # samples either side of peak to keep (~1.6s)

# Setup
script_dir    = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(script_dir, OUTPUT_FOLDER)
os.makedirs(output_folder, exist_ok=True)

# Process the csv file chosen . swings and fake_hit was done in the same way, so we can just look for all files starting with fake_hit_*.csv
swing_files = glob.glob(os.path.join(SOURCE_FOLDER, "fake_hit_*.csv"))
# We construct the full file paths for each swing CSV file found in the source folder, ensuring that 
# we can read them correctly regardless of whether the paths are absolute or relative. We then print out the number of swing CSV files found for processing.
swing_files = [os.path.join(script_dir, f) if not os.path.isabs(f)
               else f for f in glob.glob(
                   os.path.join(script_dir, SOURCE_FOLDER, "fake_hit_*.csv"))]

# We print out the number of swing CSV files found for processing.
print(f"Found {len(swing_files)} swing CSV files\n")
# We initialize two counters, total_extracted and total_skipped, to keep track of how many individual swing 
# CSV files we successfully extract and how many original CSV files we skip due to not finding any valid peaks.
total_extracted = 0
total_skipped   = 0

# We loop through each swing CSV file found in the source folder. For each file, we read it into a pandas DataFrame, 
# compute the acceleration magnitude, and use the find_peaks function from scipy to identify peaks in the acceleration 
# magnitude that exceed the defined SWING_THRESHOLD and are separated by at least PEAK_MIN_DIST samples. If no peaks are found, 
# we print a message indicating that the file is skipped and increment the total_skipped counter. If peaks are found, we extract 
# a window of data around each peak (defined by HALF_WIN) and save each window as a new CSV file in the output folder with a modified 
# filename indicating the swing number. We also print out how many swings were extracted from each original CSV file.
for filepath in sorted(swing_files):
    filename = os.path.basename(filepath)
    base     = os.path.splitext(filename)[0]  # e.g. fake_hit_20260320_100259

    df = pd.read_csv(filepath)
    acc_mag = np.sqrt(df["ax"]**2 + df["ay"]**2 + df["az"]**2).values

    # Find peaks
    peaks, props = find_peaks(acc_mag,
                               height=SWING_THRESHOLD,
                               distance=PEAK_MIN_DIST)

    if len(peaks) == 0:
        print(f"  SKIP (no peaks found): {filename}")
        total_skipped += 1
        continue

    # Extract window around each peak
    for swing_num, peak_idx in enumerate(peaks, start=1):
        start = max(0, peak_idx - HALF_WIN)
        end   = min(len(df), peak_idx + HALF_WIN)
        # We extract a window of data around each identified peak, ensuring that we do not go out of bounds of the DataFrame.
        window_df = df.iloc[start:end].copy()

        # Renumber timestamp from 0
        window_df["timestamp_s"] = window_df["timestamp_s"] - window_df["timestamp_s"].iloc[0]
        # We save each extracted window as a new CSV file in the output folder, with a filename that includes the original 
        # base name and the swing number (e.g., fake_hit_20260320_100259_s1.csv). We also increment the total_extracted counter for each swing extracted.
        out_name = f"{base}_s{swing_num}.csv"
        out_path = os.path.join(output_folder, out_name)
        # We save each extracted window as a new CSV file in the output folder, with a filename that includes the original
        window_df.to_csv(out_path, index=False)
        # We also increment the total_extracted counter for each swing extracted.
        total_extracted += 1

# We print out how many swings were extracted from each original CSV file, and at the end, 
# we print a summary of the total number of single-swing CSVs extracted, the number of files skipped due to no peaks found 
# and the location of the output folder. Finally, we provide next steps for using the extracted single-swing CSVs in the training pipeline.
    print(f"  {filename}  →  {len(peaks)} swing(s) extracted")

# We print out how many swings were extracted from each original CSV file, and at the end, we print a summary of the total number of 
# single-swing CSVs extracted, the number of files skipped due to no peaks found and the location of the output folder. 
print(f"\n{'='*60}")
print(f"Total extracted : {total_extracted} single-swing CSVs")
print(f"Total skipped   : {total_skipped} files (no peaks found)")
print(f"Output folder   : {output_folder}")
print(f"{'='*60}")

