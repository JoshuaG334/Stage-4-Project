# joshua geoghegan
# This script loads the collected accelerometer data from CSV files, identifies impact events based on a defined 
# threshold, and performs signal analysis to compare the characteristics of real impacts versus fake hits. 
# It generates visualizations of the average signal shape, peak G distribution, and frequency content for both classes of events, 
# and saves the analysis results as an image file
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.signal import find_peaks
from scipy.fft import fft, fftfreq
import glob
import os
# We set the working directory to the location of the script to ensure that all file paths are relative to this location,
os.chdir(r"")

# Configuration
SAMPLE_RATE      = 124.0
IMPACT_THRESHOLD = 8.0
DATA_FOLDER      = "data"
DARK_BG          = "#0d1117"
CARD_BG          = "#161b22"

# We define a helper function load_csv that reads a CSV file into a pandas DataFrame, checks for the required columns, 
# and computes the acceleration magnitude and gyroscope magnitude (if available) as new columns. We also add a time column based on
# the sample index and sample rate. This function returns the processed DataFrame or None if the required columns are not present.
def load_csv(filepath):
    df = pd.read_csv(filepath)
    required = ["ax", "ay", "az"]
    if not all(c in df.columns for c in required):
        return None
    df["acc_mag"] = np.sqrt(df["ax"]**2 + df["ay"]**2 + df["az"]**2)
    if "gx" in df.columns:
        df["gyro_mag"] = np.sqrt(df["gx"]**2 + df["gy"]**2 + df["gz"]**2)
    df["time"] = np.arange(len(df)) / SAMPLE_RATE
    return df

# We use the glob module to find all CSV files in the specified data folder that match the patterns for impact and fake hit events. 
# We print out the number of files found for each class to confirm that we have data to analyze. We then initialize empty lists to store 
# the extracted signal segments for impact and fake hit events, and we define the number of samples to include in each window based 
# on the sample rate and desired window duration.
def style_ax(ax, title, xlabel, ylabel):
    ax.set_facecolor(CARD_BG)
    ax.set_title(title, color="white", fontsize=10, pad=8)
    ax.set_xlabel(xlabel, color="#8b949e", fontsize=9)
    ax.set_ylabel(ylabel, color="#8b949e", fontsize=9)
    ax.tick_params(colors="#8b949e")
    ax.spines[:].set_color("#30363d")
    ax.grid(True, alpha=0.15, color="#30363d")

# We loop through each impact and fake hit CSV file, load the data using the load_csv function, and identify peaks in the acceleration 
# magnitude that exceed the defined IMPACT_THRESHOLD. For each detected peak, we extract a window of data around the peak 
# (defined by window_samples) and store it in the respective list.
impact_files  = glob.glob(os.path.join(DATA_FOLDER, "impact_*.csv"))
fakehit_files = glob.glob(os.path.join(DATA_FOLDER, "fake_hit_*.csv"))

# We print out the number of files found for each class to confirm that we have data to analyze. We then initialize empty lists to store 
# the extracted signal segments for impact and fake hit events, and we define the number of samples to include in each window based on 
# the sample rate and desired window duration.
print(f"Impact files  : {len(impact_files)}")
print(f"Fake hit files: {len(fakehit_files)}")

# We loop through each impact and fake hit CSV file, load the data using the load_csv function, and identify peaks in the acceleration magnitude
# that exceed the defined IMPACT_THRESHOLD. For each detected peak, we extract a window of data around the peak (defined by window_samples) 
# and store it in the respective list. We also handle cases where no peaks are found or where the extracted segment is shorter 
# than the desired window size by padding it with edge values.
impact_events  = []
fakehit_events = []
window_samples = int(SAMPLE_RATE * 0.4)  # ~49 samples

for filepath in impact_files:
    df = load_csv(filepath)
    if df is None: continue
    acc = df["acc_mag"].values
    peaks, _ = find_peaks(acc, height=IMPACT_THRESHOLD, distance=50)
    if len(peaks) == 0: continue
    peak = peaks[np.argmax(acc[peaks])]
    start = max(0, peak - window_samples//2)
    end   = min(len(acc), start + window_samples)
    seg   = acc[start:end]
    if len(seg) < window_samples:
        seg = np.pad(seg, (0, window_samples - len(seg)), mode='edge')
    impact_events.append(seg[:window_samples])

for filepath in fakehit_files:
    df = load_csv(filepath)
    if df is None: continue
    acc = df["acc_mag"].values
    peaks, _ = find_peaks(acc, height=IMPACT_THRESHOLD, distance=50)
    if len(peaks) == 0: continue
    peak = peaks[np.argmax(acc[peaks])]
    start = max(0, peak - window_samples//2)
    end   = min(len(acc), start + window_samples)
    seg   = acc[start:end]
    if len(seg) < window_samples:
        seg = np.pad(seg, (0, window_samples - len(seg)), mode='edge')
    fakehit_events.append(seg[:window_samples])

# We print out the number of impact and fake hit events extracted based on the detected peaks in the acceleration magnitude. 
# If no events are found for either class, we print a message indicating that there are still no events and suggest checking the 
# threshold settings before exiting the program.
print(f"Impact events  : {len(impact_events)}")
print(f"Fake hit events: {len(fakehit_events)}")

if not impact_events or not fakehit_events:
    print("Still no events - check threshold")
    exit()
# We convert the lists of impact and fake hit events into numpy arrays for easier analysis. We then compute the mean and standard deviation
# of the acceleration magnitude across all events for each class, which will be used to visualize the average signal shape and variability. 
# We also compute the time vector for the x-axis of the plots based on the number of samples and sample rate.
impact_arr  = np.array(impact_events)
fakehit_arr = np.array(fakehit_events)

impact_mean  = impact_arr.mean(axis=0)
impact_std   = impact_arr.std(axis=0)
fakehit_mean = fakehit_arr.mean(axis=0)
fakehit_std  = fakehit_arr.std(axis=0)

t_ms = (np.arange(window_samples) - window_samples//2) / SAMPLE_RATE * 1000

# We perform a Fast Fourier Transform (FFT) on the mean signals for both impact and fake hit events to analyze their frequency content. 
# We take the absolute value of the FFT results to get the magnitude spectrum, and we compute the corresponding frequency bins based on the 
# sample rate and number of samples. We also extract the peak G values for each event to analyze the distribution of peak accelerations for both classes.
impact_fft  = np.abs(fft(impact_mean))[:window_samples//2]
fakehit_fft = np.abs(fft(fakehit_mean))[:window_samples//2]
freqs       = fftfreq(window_samples, 1/SAMPLE_RATE)[:window_samples//2]

impact_peaks_g  = [s.max() for s in impact_events]
fakehit_peaks_g = [s.max() for s in fakehit_events]

# We print out the mean peak G values for both impact and fake hit events to provide a summary statistic of the typical 
# peak acceleration experienced in each class of events.
print(f"\nImpact  mean peak G : {np.mean(impact_peaks_g):.2f}G")
print(f"FakeHit mean peak G : {np.mean(fakehit_peaks_g):.2f}G")

# We create a figure with a dark background and a grid layout to display multiple subplots. We style each subplot with titles, 
# axis labels, and colors that match the overall theme.
fig = plt.figure(figsize=(14, 10))
fig.patch.set_facecolor(DARK_BG)
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

# We plot the average signal shape for both impact and fake hit events in the first subplot, including shaded areas to represent the standard deviation. 
# We also add a vertical dashed line to indicate the location of the peak (time zero) and include a legend to differentiate between the two classes. 
# In the second subplot, we create histograms of the peak G values for both classes to visualize their distributions.
ax1 = fig.add_subplot(gs[0, :2])
style_ax(ax1, "Average Signal: Impact vs Fake Hit (aligned to peak)", "Time from peak (ms)", "Acceleration (G)")
ax1.plot(t_ms, impact_mean,  color="#3fb950", linewidth=2, label=f"Impact (n={len(impact_events)})")
ax1.fill_between(t_ms, impact_mean-impact_std, impact_mean+impact_std, color="#3fb950", alpha=0.15)
ax1.plot(t_ms, fakehit_mean, color="#f85149", linewidth=2, label=f"Fake Hit (n={len(fakehit_events)})")
ax1.fill_between(t_ms, fakehit_mean-fakehit_std, fakehit_mean+fakehit_std, color="#f85149", alpha=0.15)
ax1.axvline(0, color="white", linestyle="--", linewidth=0.8, alpha=0.5, label="Peak")
ax1.legend(facecolor=CARD_BG, labelcolor="white", fontsize=9)

ax2 = fig.add_subplot(gs[0, 2])
style_ax(ax2, "Peak G Distribution", "Peak G (G)", "Count")
ax2.hist(impact_peaks_g,  bins=12, color="#3fb950", alpha=0.7, label="Impact")
ax2.hist(fakehit_peaks_g, bins=12, color="#f85149", alpha=0.7, label="Fake Hit")
ax2.legend(facecolor=CARD_BG, labelcolor="white", fontsize=9)

ax3 = fig.add_subplot(gs[1, :2])
style_ax(ax3, "Frequency Content (FFT)", "Frequency (Hz)", "Magnitude")
ax3.plot(freqs, impact_fft,  color="#3fb950", linewidth=1.5, label="Impact")
ax3.plot(freqs, fakehit_fft, color="#f85149", linewidth=1.5, label="Fake Hit")
ax3.set_xlim(0, SAMPLE_RATE/2)
ax3.legend(facecolor=CARD_BG, labelcolor="white", fontsize=9)

ax4 = fig.add_subplot(gs[1, 2])
ax4.set_facecolor(CARD_BG)
ax4.axis("off")
style_ax(ax4, "Statistical Summary", "", "")
stats = [
    ("",             "Impact",                        "Fake Hit"),
    ("Mean Peak G",  f"{np.mean(impact_peaks_g):.1f}G",  f"{np.mean(fakehit_peaks_g):.1f}G"),
    ("Max Peak G",   f"{np.max(impact_peaks_g):.1f}G",   f"{np.max(fakehit_peaks_g):.1f}G"),
    ("Std Peak G",   f"{np.std(impact_peaks_g):.1f}G",   f"{np.std(fakehit_peaks_g):.1f}G"),
    ("Events",       str(len(impact_events)),             str(len(fakehit_events))),
]
# We display a statistical summary of the peak G values for both impact and fake hit events in the fourth subplot. 
# We create a simple table-like layout using text annotations, where we list the mean, max, and standard deviation of the peak G values, 
# as well as the total number of events for each class. We use different colors to differentiate between the impact and fake hit
# columns and we add a title to this section of the figure.
y = 0.92
for row in stats:
    if row[0] == "":
        ax4.text(0.35, y, row[1], color="#3fb950", fontsize=9, fontweight="bold", transform=ax4.transAxes, ha="center")
        ax4.text(0.75, y, row[2], color="#f85149", fontsize=9, fontweight="bold", transform=ax4.transAxes, ha="center")
    else:
        ax4.text(0.02, y, row[0], color="#8b949e", fontsize=9, transform=ax4.transAxes)
        ax4.text(0.45, y, row[1], color="#3fb950", fontsize=9, transform=ax4.transAxes, ha="center")
        ax4.text(0.78, y, row[2], color="#f85149", fontsize=9, transform=ax4.transAxes, ha="center")
    y -= 0.13
# We add a title to the entire figure, save it as a PNG file with a descriptive name, and display the figure. The saved image will 
# contain all the analysis results for easy reference and sharing.
fig.suptitle("Smart Hurley - Impact vs Fake Hit Signal Analysis", color="white", fontsize=13, y=0.98)
plt.savefig("analysis_impact_vs_fakehit.png", dpi=150, bbox_inches="tight", facecolor=DARK_BG)
print("Saved: analysis_impact_vs_fakehit.png")
plt.show()