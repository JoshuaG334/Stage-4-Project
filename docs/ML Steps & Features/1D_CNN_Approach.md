# Smart Hurl — 1D CNN Motion Classifier

A technical overview of how the 1D Convolutional Neural Network works in the Smart Hurl project, from raw IMU data on the Arduino Nano 33 BLE Sense Rev2 to a classification result sent over BLE to the Android app.

---

## Overview

The Smart Hurl system classifies hurley motion into four classes in real time on an embedded microcontroller:

| Class | Label | Description |
|-------|-------|-------------|
| 0 | Idle | No significant motion |
| 1 | Swing | Full hurley swing without ball contact |
| 2 | Impact | Genuine ball strike |
| 3 | Fake Hit | Deceptive swing motion |

Classification runs entirely on device using a quantised TensorFlow Lite Micro model no data is sent to a server during inference.

---

## Why a 1D CNN?

The earlier approach used a feature based MLP (Multi Layer Perceptron) that required manually extracting 31 statistical features (mean, std, RMS, skewness, kurtosis etc.) from each window before inference. While this achieved 92% accuracy, it required significant pre processing code on the Arduino and was sensitive to the quality of the hand crafted features.

The 1D CNN takes the **raw sensor readings** as input and learns its own feature representations during training. This removes the manual feature engineering step entirely and achieved **96% accuracy** on the same dataset with a 100 sample window, compared to 86% for the CNN at 50 samples demonstrating that the larger context window was critical for capturing the full motion arc.

---

## Input: Sliding Window

The IMU on the Arduino Nano 33 BLE Sense Rev2 (BMI270 accelerometer + BMM150 gyroscope) is sampled at approximately **125 Hz** (one sample every 8 ms).

Each sample contains 6 channels:

```
[ax, ay, az, gx, gy, gz]
```

These samples are collected into a **circular buffer of 100 samples**, giving a window of approximately **800 ms** of motion long enough to capture a full swing arc including the follow through.

```
Window shape: (100 samples) × (6 channels) = 600 values
```

---

## Pre-processing: Per Channel Normalisation

Before passing the window to the model, each channel is normalised using the mean and standard deviation computed from the full training dataset:

```
normalised = (raw_value - CHANNEL_MEAN[c]) / CHANNEL_STD[c]
```

The `CHANNEL_MEAN` and `CHANNEL_STD` arrays are pre computed during training and baked directly into the Arduino header file (`hurley_cnn_model.h`), so no runtime statistics are needed.

This ensures the model receives input in the same scale as the training data regardless of sensor orientation or baseline drift.

---

## Model Architecture
- finish this part *****

**What the convolutional layers learn:**
- The first Conv1D layer slides a filter of width 5 samples (~40ms) along the time axis across all 6 channels simultaneously, learning short duration patterns like the onset of a sharp acceleration spike.
- The second Conv1D layer operates on the pooled output and learns to combine these short patterns into longer motion signatures for example, the combination of a spike followed by rapid decay that characterises a genuine impact.
- GlobalAveragePooling collapses the entire time axis into a single feature vector, making the classifier position invariant within the window.

---

## Feedforward Inference on the Arduino

On each 8 ms timer tick the Arduino executes the following pipeline:

```
1. Read IMU sample → [ax, ay, az, gx, gy, gz]
2. Write into circular buffer at current index
3. Increment index (wraps at 100)
4. If buffer not yet full → skip inference
5. Check activity gate: if magnitude < 1.8G → skip (device is idle)
6. Normalise all 600 values using CHANNEL_MEAN / CHANNEL_STD
7. Copy into TFLite input tensor
8. Call interpreter->Invoke()  ← runs CNN on device (~5ms)
9. Read output tensor: 4 softmax probabilities
10. Take argmax → winning class + confidence %
11. Apply cooldown timers (500ms general, 1500ms impact)
12. Build JSON string and send over BLE
```

The entire inference pipeline runs in a few milliseconds on the Cortex-M4F at 64 MHz, well within the 8 ms sampling interval.

---

## Output: BLE JSON Payload

After each classification event the result is sent to the Android app as a JSON string over BLE:

```json
{"cls":2,"conf":94,"peakG":18.3,"lambda":22.4}
```

| Field | Description |
|-------|-------------|
| `cls` | Class index: 0=idle, 1=swing, 2=impact, 3=fake_hit |
| `conf` | Model confidence as a percentage (0–100) |
| `peakG` | Peak acceleration magnitude in G recorded during the window |
| `lambda` | Vibration decay proxy only meaningful for cls==2, else 0.0 |

The `lambda` value is computed using a **peak relative decay method**: the algorithm finds the peak acceleration sample index, takes the mean of the 15 samples immediately following it, and computes `(peak / decay_mean) × 8`. A high lambda indicates rapid post impact damping consistent with a sweet spot strike; a low lambda indicates slower decay consistent with an off center hit.

---

## Sweet Spot Rating Thresholds

The Android app converts the lambda value into a star rating displayed after each impact:

| Lambda | Rating | Meaning |
|--------|--------|---------|
| ≥ 25 | 3 star Sweet Spot | Clean center of percussion strike |
| 15 – 25 | 2 star Good Contact | Solid contact, slightly off center |
| < 15 | 1 star Off Center | Poor contact, vibration persists |

These thresholds were calibrated empirically from analysis of 149 recorded impact events collected across multiple sessions.

---

## Model Size and Constraints

| Metric | Value |
|--------|-------|
| Training accuracy | 96% (100 sample window) |
| Model size (TFLite INT8) | ~18 KB flash |
| Tensor arena (RAM) | 48 KB |
| Nano flash available | 1 MB |
| Nano RAM available | 256 KB |

The model fits comfortably within the Nano's constraints with significant headroom.

---
