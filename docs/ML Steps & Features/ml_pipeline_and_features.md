# Smart Hurley - TinyML Pipeline & Feature Explanation

# Joshua Geoghegan 
# 3/27/2026

# Smart Hurley with TinyML 

---

## The Pipeline - Step by Step

### Step 1  `1_build_dataset_final.py`

This script goes through all CSV recordings and converts raw sensor data into a structured dataset the model can learn from.

For every recording it slides a **50-sample window** (~0.4 seconds at 124Hz) along the data in steps of 3 samples. For impact files specifically it only extracts windows centred around the actual peak this was the key fix that stopped swing motion being mislabelled as impact.

For each window it computes **28 features** mathematical summaries that describe what the motion looks like. These 28 numbers replace the 300 raw values (50 samples × 6 axes), making the data compact and meaningful. The result is saved to `dataset.csv` with each row being one window and its label.

---

### Step 2  `2_train_model_final.py`

This script takes `dataset.csv` and trains a small neural network on it. First it normalises all 28 features using `StandardScaler` so no single feature dominates due to scale differences. Then it splits the data 80/20 into training and test sets.

The neural network has three layers 32 neurons, then 16 neurons, then 4 output neurons (one per class). Each epoch it sees all the training data, measures how wrong it is using categorical crossentropy loss, and adjusts its weights slightly to improve. After training it converts the model to TensorFlow Lite with int8 quantisation, shrinking it from ~200KB to a few KB so it fits on the Arduino. It also saves the scaler parameters to `model_info.json` so the Arduino can normalise its data the same way.

---

### Step 3 - `3_convert_to_arduino_final.py`

This takes the `.tflite` binary file and converts every byte into a C hex value, producing `hurley_model.h`. This header file contains the model weights, the scaler means and scales, and the class names everything the Arduino needs baked into one file it can include directly.

---

## The 28 Features Explained

### Acceleration Magnitude Features (5)

The magnitude `sqrt(ax² + ay² + az²)` is orientation invariant it does not matter which way the hurley is pointing, the magnitude is always the same. From this signal across the 50 sample window the following are extracted:

| Feature | What it captures |
|---|---|
| `acc_mag_mean` | Average acceleration level separates idle (~1G) from active motion |
| `acc_mag_std` | How much the signal varied  smooth for swing, spiky for impact |
| `acc_mag_max` | Peak acceleration  most powerful single feature for detecting impacts |
| `acc_mag_min` | Lowest acceleration helps detect free swing (near zero G during follow through) |
| `acc_mag_rms` | Root mean square  similar to mean but more sensitive to peaks |

---

### Gyroscope Magnitude Features (5)

The same five statistics applied to the gyroscope magnitude `sqrt(gx² + gy² + gz²)`. The gyroscope captures rotational speed a swing produces high sustained gyro while an impact produces a sharp gyro drop as the hurley decelerates on contact.

| Feature | What it captures |
|---|---|
| `gyro_mag_mean` | Average rotational speed - high for swings, low for idle and impact |
| `gyro_mag_std` | Variation in rotation - helps distinguish swing style |
| `gyro_mag_max` | Peak rotation - swing peak is high and sustained |
| `gyro_mag_min` | Minimum rotation - near zero for idle |
| `gyro_mag_rms` | Overall rotational energy across the window |

---

### Per-Axis Statistics (12)

Mean and standard deviation for each of the six individual axes `ax`, `ay`, `az`, `gx`, `gy`, `gz`. While the magnitudes are orientation invariant, the per axis values give the model context about the direction of motion. A swing along a specific axis will show high variance on that axis. These 12 features help the model distinguish between different swing directions and orientations.

---

### Rate of Change  `acc_mag_diff_max` (1)

The largest single sample jump in acceleration magnitude within the window. This directly captures the sharpness of the onset of an event. A real ball strike produces an extremely sharp instantaneous spike, whereas a swing builds up gradually. This feature alone can separate sharp events from smooth ones.

---

### Skewness  `acc_mag_skew` (1)

Measures the asymmetry of the acceleration distribution within the window. A real impact has a very sharp one sided spike the signal shoots up fast and comes down more slowly giving high positive skew. A smooth swing is more symmetric. This helps distinguish sharp impact events from sustained motion.

---

### Kurtosis  `acc_mag_kurtosis` (1)

Measures how impulsive the signal is how much of the energy is concentrated in a single sharp peak versus spread across the window. A genuine ball strike produces an extremely narrow tall peak giving very high kurtosis. Fake hits tend to be broader and flatter. This is one of the strongest features for separating real impacts from fake hits.

---

### Peak to Mean Ratio  `acc_peak_to_mean` (1)

The maximum acceleration divided by the mean. This is very high for impacts one big spike dwarfs the average and moderate for swings where the whole window is elevated. Helps confirm whether a window contains a single sharp event or sustained motion.

---

### Peak to Std Ratio `acc_peak_to_std` (1)

The maximum acceleration divided by the standard deviation. This measures how many standard deviations above typical the peak is. A genuine impact spike is extremely far above average, giving a very high value. Works together with kurtosis to confirm the sharpness of impact events.

---

### Gyro Peak to Mean Ratio `gyro_peak_to_mean` (1)

The maximum gyroscope magnitude divided by the mean. During a real impact the hurley decelerates suddenly on contact the gyro drops sharply so the peak before contact is very high relative to the mean across the window. During a swing the gyro stays elevated throughout so this ratio is lower. This helps the model detect the characteristic deceleration signature of ball contact.

---

### Jerk Features `jerk_max`, `jerk_mean`, `jerk_std` (3)

Jerk is the rate of change of acceleration magnitude, computed as:

```
jerk = |acc_mag[i+1] - acc_mag[i]| × sample_rate   (units: G/s)
```

These three features capture how violently the acceleration changes within the window.

| Class | Mean Peak Jerk | Interpretation |
|---|---|---|
| Swing | 111.6 G/s | Smooth continuous motion |
| Impact | 672.4 G/s | Sharp ball contact |
| Fake hit | 1878.4 G/s | Instantaneous hard surface stop |

Fake hits have nearly **3x higher jerk** than real impacts because a hard surface (ground, wall) stops the hurley almost instantly, whereas a ball has elasticity and absorbs the impact over a slightly longer time. These three features were the final addition to the model and directly target the impact vs fake hit confusion that was the hardest classification problem.

---

## Feature Summary Table

| # | Feature | Group | Primary Use |
|---|---|---|---|
| 1 | acc_mag_mean | Acc magnitude | Idle vs active |
| 2 | acc_mag_std | Acc magnitude | Spike sharpness |
| 3 | acc_mag_max | Acc magnitude | Impact detection |
| 4 | acc_mag_min | Acc magnitude | Swing follow through |
| 5 | acc_mag_rms | Acc magnitude | Overall energy |
| 6 | gyro_mag_mean | Gyro magnitude | Swing vs impact |
| 7 | gyro_mag_std | Gyro magnitude | Rotation variation |
| 8 | gyro_mag_max | Gyro magnitude | Swing peak |
| 9 | gyro_mag_min | Gyro magnitude | Idle detection |
| 10 | gyro_mag_rms | Gyro magnitude | Rotational energy |
| 11-12 | ax_mean, ax_std | Per-axis | Swing direction |
| 13-14 | ay_mean, ay_std | Per-axis | Swing direction |
| 15-16 | az_mean, az_std | Per-axis | Swing direction |
| 17-18 | gx_mean, gx_std | Per-axis | Rotation axis |
| 19-20 | gy_mean, gy_std | Per-axis | Rotation axis |
| 21-22 | gz_mean, gz_std | Per-axis | Rotation axis |
| 23 | acc_mag_diff_max | Rate of change | Spike sharpness |
| 24 | acc_mag_skew | Shape | Impact asymmetry |
| 25 | acc_mag_kurtosis | Shape | Impulsiveness |
| 26 | acc_peak_to_mean | Ratio | Sharp event detection |
| 27 | acc_peak_to_std | Ratio | Spike significance |
| 28 | gyro_peak_to_mean | Ratio | Deceleration on contact |
| 29-31 | jerk_max/mean/std | Jerk | Impact vs fake hit |

> **Note:** The model was trained with 28 features (indices 1–28 above). The jerk features (29–31) were added in the final training run bringing the total to 28 features as `NUM_FEATURES` in `hurley_model.h`.

---

## Note on Decay Rate

The exponential decay rate (lambda λ) was analysed as a **standalone tool** (`decay_rate_analysis.py`) rather than as a model feature. Computing a proper exponential curve fit using `scipy.optimize.curve_fit` is too computationally expensive for real-time inference on a microcontroller.

A lightweight decay approximation is included in `hurley_ble.ino`:

```cpp
float first_half_max  = f_max(acc_mag, WINDOW_SIZE/2);
float second_half_max = f_max(acc_mag + WINDOW_SIZE/2, WINDOW_SIZE/2);
decay_est = (second_half_max > 0.1) ? first_half_max / second_half_max : 10.0;
```

This compares the peak of the first half of the window to the peak of the second half. A high ratio indicates fast decay consistent with a sweet spot strike.

---

*Smart Hurley Project - TU Dublin 2026*
