# Smart Hurley - Neural Network Architecture

**Author:** Joshua Geoghegan  
**Project:** Smart Hurley with TinyML  
**TU Dublin - BEng (Hons) Computer Engineering - Mobile Systems**

---

## Neural Network Architecture

### Overview

The model is a lightweight feedforward neural network designed to run efficiently after TensorFlow Lite quantisation on the Arduino Nano 33 BLE Sense Rev2. The architecture balances classification accuracy against the strict memory and compute constraints of an embedded microcontroller.

```
┌─────────────────────────────────────┐
│         INPUT LAYER                 │
│         28 features                 │
│  (normalised using StandardScaler)  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       DENSE LAYER 1                 │
│       32 neurons                    │
│       Activation: ReLU              │
│       Parameters: 28×32 + 32 = 928  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       DROPOUT 1                     │
│       Rate: 20%                     │
│       (training only)               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       DENSE LAYER 2                 │
│       16 neurons                    │
│       Activation: ReLU              │
│       Parameters: 32×16 + 16 = 528  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       DROPOUT 2                     │
│       Rate: 10%                     │
│       (training only)               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       OUTPUT LAYER                  │
│       4 neurons                     │
│       Activation: Softmax           │
│       Parameters: 16×4 + 4 = 68     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       OUTPUT                        │
│  [idle, swing, impact, fake_hit]    │
│  Probabilities summing to 1.0       │
│  Threshold: 80% confidence          │
└─────────────────────────────────────┘

Total trainable parameters: 1,524
```

---

### Layer by Layer Explanation

#### Input Layer - 28 Features
The 28 extracted features are normalised using `StandardScaler` before being fed into the network. Normalisation ensures each feature has a mean of 0 and standard deviation of 1 so no single feature dominates due to scale differences. The scaler parameters (means and scales) are baked into `hurley_model.h` so the Arduino applies identical normalisation at inference time.

---

#### Dense Layer 1 - 32 Neurons, ReLU
Each of the 32 neurons computes a weighted sum of all 28 inputs plus a bias term, then passes the result through the ReLU (Rectified Linear Unit) activation function.

**ReLU formula:**
```
output = max(0, weighted_sum + bias)
```

ReLU introduces non-linearity without it the entire network would collapse to a single linear transformation and could not learn complex patterns. The 32 neurons collectively learn 32 different patterns to detect in the feature space, such as high peak G, high jerk, high kurtosis combinations. This layer has **928 trainable parameters** (28 × 32 weights + 32 biases).

---

#### Dropout Layer 1 - 20%
During training, 20% of the 32 neurons are randomly disabled each batch. This prevents the network from relying too heavily on any single neuron and forces it to learn redundant, generalisable representations a technique called **regularisation**. This directly combats overfitting where the model memorises training data but fails on unseen data. Dropout is disabled during inference on the Arduino.

---

#### Dense Layer 2 - 16 Neurons, ReLU
Takes the 32 outputs from layer 1 as its inputs. This layer learns higher level combinations of the patterns detected by layer 1. For example, layer 1 may detect high peak G and high jerk independently, while layer 2 combines these into a representation meaning *"this window contains a sharp impulsive event."* The network narrows from 32 to 16 neurons here, compressing the representation to the most discriminative combinations before making a final class decision. This layer has **528 trainable parameters** (32 × 16 weights + 16 biases).

---

#### Dropout Layer 2 - 10%
A lighter dropout of 10% is applied at this stage. Less aggressive regularisation is needed here as the network is close to producing a final decision and over regularisation at this point could reduce accuracy.

---

#### Output Layer - 4 Neurons, Softmax
One neuron per class: idle, swing, impact, fake_hit. Each neuron produces a raw score. The **Softmax** activation converts these four scores into four probabilities that sum to exactly 1.0.

**Softmax formula:**
```
P(class_i) = exp(score_i) / sum(exp(score_j) for all j)
```

**Example output:**
```
idle:     0.02  (2%)
swing:    0.05  (5%)
impact:   0.91  (91%)  ← predicted class
fake_hit: 0.02  (2%)
```

The class with the highest probability is the prediction. The confidence threshold of 80% means the Arduino only reports a classification if one class scores above 0.80, suppressing uncertain predictions. This layer has **68 trainable parameters** (16 × 4 weights + 4 biases).

---

### Training Configuration

| Parameter | Value | Reason |
|---|---|---|
| Optimiser | Adam | Adaptive learning rate, fast convergence |
| Loss function | Categorical crossentropy | Standard for multi-class classification |
| Epochs | 150 max | Early stopping prevents over training |
| Batch size | 16 | Small batches generalise better on small datasets |
| Early stopping patience | 20 epochs | Stops if validation loss doesn't improve |
| Test split | 20% | Standard train/test split |
| Quantisation | INT8 | Reduces model size for Arduino deployment |

---

### Final Model Performance

| Class | Precision | Recall | F1 Score |
|---|---|---|---|
| idle | 0.95 | 1.00 | 0.97 |
| swing | 0.92 | 0.91 | 0.92 |
| impact | 0.89 | 0.84 | 0.87 |
| fake_hit | 0.95 | 0.95 | 0.95 |
| **Overall accuracy** | | | **0.93** |

---

### Why This Architecture Size

The network is intentionally small. At 1,524 total parameters it is tiny by modern ML standards but sufficient for a 4-class problem with 28 well engineered features. A larger network would achieve marginally higher accuracy on training data but would be harder to quantise and deploy on the Arduino Nano 33 BLE Sense Rev2 which has 256KB flash and 32KB RAM. The TFLite quantised model occupies approximately 8–12KB of flash well within the available memory alongside the TFLite Micro runtime.

---

*Smart Hurley Project - TU Dublin 2026*
