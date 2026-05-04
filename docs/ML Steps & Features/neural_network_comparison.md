# Smart Hurl — Neural Network Model Comparison

A complete record of all neural network configurations investigated during this project, including architectural choices, dataset adjustments, and the performance impact of each change.

---

## Overview

Five model configurations were developed and evaluated across two fundamentally different approaches: a hand-engineered feature-based MLP and a raw-waveform 1D CNN. Each iteration addressed a specific weakness identified from the confusion matrices of the previous configuration.

| # | Model | Window | Dataset | Accuracy | Flash (KB) |
|---|-------|--------|---------|----------|------------|
| 1 | Feature-Based MLP | 50 samples | Original (81,479 windows) | 92% | 5.86 |
| 2 | 1D CNN | 50 samples | Original (125,239 windows) | 86% | ~18 |
| 3 | 1D CNN | 100 samples | Original (125,239 windows) | 96% | 25.7 |
| 4 | Feature-Based MLP | 100 samples | Original | 93% | 5.86 |
| 5 | 1D CNN | 100 samples | Refined (114,751 windows) | **98%** | 25.7 |

**Model 5 was selected for final deployment.**

---

## Model 1 — Feature-Based MLP (50 samples)

### Architecture

```
Input(31) → Dense(32, ReLU) → Dropout(0.2) → Dense(16, ReLU) → Dropout(0.1) → Dense(4, Softmax)
```

### Input
- Window size: **50 samples** (~400 ms at ~125 Hz)
- **31 hand-engineered statistical features** extracted per window:
  - Acceleration magnitude: mean, std, max, min, RMS
  - Gyroscope magnitude: mean, std, max, min, RMS
  - Per-axis (ax, ay, az, gx, gy, gz): mean, std — 12 features
  - Acceleration magnitude extras: max absolute diff between consecutive samples, skewness, kurtosis
  - Ratio features: peak-to-mean and peak-to-std of accel magnitude, peak-to-mean of gyro magnitude
  - Jerk features (added after signal analysis): max jerk, mean jerk, std jerk
- Normalisation: **StandardScaler** (mean/std per feature, computed across training set, saved to `scaler.pkl`)

### Training Configuration
| Parameter | Value |
|-----------|-------|
| Optimiser | Adam |
| Loss | Categorical cross-entropy |
| Max epochs | 150 |
| Batch size | 16 |
| Train/test split | 80/20 stratified |
| Early stopping | patience=20, restore best weights |
| Quantisation | INT8 post-training (TFLite) |

### Dataset
- Total windows: **81,479**
- idle: 21,731 · swing: 22,388 · impact: 15,680 · fake_hit: 21,680
- Impact windows extracted using **peak-centred windowing** (±250 samples around peaks > 8G) to avoid labelling swing-contaminated windows as impact
- All other classes: standard sliding window with step size 3

### Results

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| Idle | — | 97.8% | 0.96 |
| Swing | — | 85.4% | 0.89 |
| Impact | — | 86.6% | 0.87 |
| Fake Hit | — | 93.8% | 0.94 |
| **Overall** | | | **92%** |

### Key weaknesses
- Swing → Impact confusion: **11.9%** of swing windows misclassified as impact (physically expected — impact is the terminal phase of a swing)
- Impact recall lower than expected due to swing context contaminating some windows

---

## Model 2 — 1D CNN (50 samples)

### Architecture

```
Input(50, 6)
→ Conv1D(32, kernel=5, ReLU, same) → BatchNorm → MaxPool(2) → Dropout(0.2)
→ Conv1D(64, kernel=3, ReLU, same) → BatchNorm → MaxPool(2) → Dropout(0.2)
→ GlobalAveragePooling1D
→ Dense(64, ReLU) → Dropout(0.3)
→ Dense(4, Softmax)
```

### Input
- Window size: **50 samples** (~400 ms)
- Raw 6-axis IMU values — shape **(50, 6)** — no feature extraction
- Normalisation: **per-channel mean/std** (computed across training set, stored in `channel_means.npy` / `channel_stds.npy`)

### Training Configuration
| Parameter | Value |
|-----------|-------|
| Optimiser | Adam |
| Loss | Categorical cross-entropy |
| Max epochs | 150 |
| Batch size | 32 |
| Train/test split | 80/20 stratified |
| Early stopping | patience=20, restore best weights |
| Quantisation | INT8 post-training (TFLite) |

### Dataset
- Total windows: **125,239** (original, multi-motion CSVs)
- idle: 37,637 · swing: 32,522 · impact: 20,785 · fake_hit: 34,295
- Same peak-centred windowing for impact class

### Results

| Class | Recall | F1 |
|-------|--------|-----|
| Idle | 75.2% | 0.84 |
| Swing | 85.1% | 0.90 |
| Impact | 91.7% | 0.87 |
| Fake Hit | 95.1% | 0.85 |
| **Overall** | | **86%** |

### Key weaknesses
- **Idle → Fake Hit confusion: 22.2%** — major failure mode. Brief incidental wrist movements in idle windows superficially resemble fake hit acceleration transients when viewed as a raw 50-sample sequence. The CNN lacked sufficient temporal context to distinguish them.
- Swing → Impact confusion: 13.1%

### Why it underperformed the MLP at this window size
The MLP's hand-engineered features (particularly jerk onset rate, gyroscope magnitude, and peak-to-mean ratio) provide an explicit statistical summary of the window that compresses physically meaningful discriminative information into 31 scalars before the model sees the data. The CNN must discover these patterns from 300 raw values with insufficient temporal context at 50 samples.

---

## Model 3 — 1D CNN (100 samples) ← major improvement

### Change from Model 2
**Window size doubled from 50 to 100 samples** (~800 ms). This was the single largest performance gain across all experiments: a **10 percentage point improvement** from 86% to 96%.

### Architecture
Identical to Model 2, with input shape changed to **(100, 6)**.

```
Input(100, 6)
→ Conv1D(32, kernel=5, ReLU, same) → BatchNorm → MaxPool(2) → Dropout(0.2)
→ Conv1D(64, kernel=3, ReLU, same) → BatchNorm → MaxPool(2) → Dropout(0.2)
→ GlobalAveragePooling1D
→ Dense(64, ReLU) → Dropout(0.3)
→ Dense(4, Softmax)
```

### Input
- Window size: **100 samples** (~800 ms)
- Raw 6-axis IMU values — shape **(100, 6)**
- Same per-channel normalisation as Model 2

### Training Configuration
Identical to Model 2 (Adam, batch size 32, 150 epochs max, early stopping patience 20).

### Dataset
Same original dataset as Model 2 (125,239 windows — multi-motion CSVs).

### Results

| Class | Recall | F1 |
|-------|--------|-----|
| Idle | 94.3% | 0.95 |
| Swing | 97.3% | 0.98 |
| Impact | 97.8% | 0.97 |
| Fake Hit | 95.3% | 0.94 |
| **Overall** | | **96%** |

### Why the window size made such a difference
- The 800 ms window allows the CNN to observe the full swing buildup before the impact peak, making swing vs. impact boundaries unambiguous
- Swing → Impact confusion dropped from **13.1% → 1.6%**
- Idle → Fake Hit confusion dropped from **22.2% → 5.5%** — the longer context makes brief incidental transients far less prominent relative to the overall window statistics learned by the convolutional filters

### Embedded resource impact
- Flash: 25.7 KB (vs ~18 KB for 50-sample CNN) — still well within 1 MB
- Tensor arena: 48 KB RAM (vs ~10 KB for MLP) — within 256 KB

---

## Model 4 — Feature-Based MLP (100 samples)

### Change from Model 1
Window size increased to 100 samples to match the CNN investigation. Features remain the same 31 statistics but computed over a longer window.

### Results

| Class | Recall | F1 |
|-------|--------|-----|
| Idle | 99.3% | 0.97 |
| Swing | 92.3% | 0.91 |
| Impact | 81.2% | 0.85 |
| Fake Hit | 95.5% | 0.95 |
| **Overall** | | **93%** |

### Observations
- Only a modest 1 percentage point improvement (92% → 93%) versus the CNN's 10 point gain
- Impact recall **regressed to 81.2%** (from 86.6% at 50 samples) — the longer window captures more swing context around the impact peak, making it harder for the statistical features to distinguish impact from swing at a summary level
- This demonstrates that hand-engineered statistical features benefit far less from additional temporal context than an end-to-end learned approach, because features like mean and RMS aggregate the window regardless of temporal order

---

## Model 5 — 1D CNN (100 samples, Refined Dataset) ← deployed model

### Change from Model 3
**Dataset refinement**: the original multi-motion CSV files contained three consecutive motions per file. Transitions between motions introduced label boundary noise — windows spanning two consecutive motions received an incorrect label. A peak detection algorithm was used to segment each multi-motion swing and fake_hit CSV into individual single-motion files, extracting a window of 200 samples either side of each detected peak. This produced **224 single-motion swing CSVs** and a matching set of single-motion fake_hit CSVs.

### Architecture
Identical to Model 3 — no architectural changes, only the training data changed.

### Dataset
- Total windows: **114,751** (refined)
- idle: 35,986 · swing: 21,805 · impact: 31,607 · fake_hit: 25,353
- Swing and fake_hit counts reduced after eliminating inter-motion boundary windows

### Results

| Class | Recall | F1 |
|-------|--------|-----|
| Idle | 98.4% | 0.97 |
| Swing | 98.0% | 0.98 |
| Impact | 98.5% | 0.99 |
| Fake Hit | 96.0% | 0.97 |
| **Overall** | | **98%** |

### Impact of dataset refinement
- Idle → Fake Hit confusion reduced from **512 misclassified windows → 100** (−80%)
- Swing → Impact confusion reduced from **279 windows → 39** (−86%)
- Swing precision improved to **99%**, impact precision improved to **99%**
- Root cause confirmed: inter-motion transition regions in multi-motion CSV files were the primary source of both confusion types — windows at these boundaries contained mixed-class signal that the model could not cleanly separate regardless of architecture

### Why this was selected for deployment
1. Highest overall accuracy: **98%**
2. Smallest inference preprocessing: only per-channel normalisation (no feature extraction pipeline), reducing firmware complexity and risk of implementation error
3. Model size (25.7 KB) and tensor arena (48 KB) well within Arduino Nano 33 BLE Sense Rev2 hardware limits
4. JSON BLE payload (cls, conf, peakG, λ) unchanged from the MLP firmware — Android app required no modification

---

## Summary of Design Decisions

| Decision | Reason | Effect |
|----------|--------|--------|
| Added 3 jerk features to MLP (28 → 31) | Signal analysis showed fake hits produce ~3× higher jerk than real impacts | Improved fake_hit discrimination in MLP |
| Switched to peak-centred windowing for impact class | Sliding window across full recording labelled swing-contaminated windows as impact | Reduced label noise in impact class |
| Doubled CNN window from 50 → 100 samples | 50-sample CNN showed 22.2% idle→fake_hit confusion due to insufficient temporal context | +10 pp accuracy, eliminated primary failure mode |
| Refined swing/fake_hit CSVs to single-motion files | Multi-motion recordings introduced boundary noise at class transitions | +2 pp accuracy, −80% idle→fake_hit confusion |
| Selected CNN over MLP for deployment | CNN (98%) outperforms MLP (93%) at 100-sample windows; simpler inference preprocessing | Best accuracy, simpler embedded firmware |

---

## Embedded Deployment Specifications (Final Model)

| Metric | Value |
|--------|-------|
| Architecture | 1D CNN |
| Input shape | (100, 6) — raw IMU window |
| Quantisation | INT8 post-training (TFLite Micro) |
| Flash storage | 25.7 KB |
| Tensor arena (RAM) | 48 KB |
| Inference preprocessing | Per-channel normalisation only |
| Overall accuracy | 98% |
| Target hardware | Arduino Nano 33 BLE Sense Rev2 (nRF52840, Cortex-M4F, 64 MHz) |
| Firmware file | `BLE_To_android_app.ino` |
| Model header | `hurley_cnn_model.h` |
