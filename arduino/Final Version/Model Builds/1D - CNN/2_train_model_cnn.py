# Joshua Geoghegan
# Smart Hurley - 1D CNN Model Training
# Operates directly on raw IMU signal windows (50 timesteps x 6 channels)
# rather than hand-crafted statistical features.
#
# The CNN learns filters that respond to signal shapes over time -
# including the acceleration spike, jitter, and post-impact decay
# that characterise a real hurley strike.
#
# Architecture:
#   Conv1D(32) -> Conv1D(64) -> GlobalAvgPool -> Dense(64) -> Dense(4)
#
# Compare confusion matrix output against feature-based approach
# (2_train_model_final.py) to evaluate which method works better.

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import json
import os

# Configuration
INPUT_X         = "model/X_raw.npy"
INPUT_Y         = "model/y_raw.npy"
MODEL_TFLITE    = "model/hurley_cnn_model.tflite"
MODEL_INFO_FILE = "model/model_info_cnn.json"

LABEL_NAMES  = {0: "idle", 1: "swing", 2: "impact", 3: "fake_hit"}
NUM_CLASSES  = 4
WINDOW_SIZE  = 100
NUM_CHANNELS = 6      # ax, ay, az, gx, gy, gz
EPOCHS       = 150
BATCH_SIZE   = 32
TEST_SIZE    = 0.2
RANDOM_STATE = 42

# Ensure model directory exists
os.makedirs("model", exist_ok=True)

# Load
print("Loading dataset...")
# We load the preprocessed dataset from the .npy files created in the previous step. 
# The X array contains the raw IMU signal windows, and the y array contains the corresponding labels for each window.
X = np.load(INPUT_X)   # shape: (N, 50, 6)
y = np.load(INPUT_Y)   # shape: (N,)

# Summary
# We print a summary of the dataset, including the total number of windows, the shapes of X and y, 
# and a breakdown of how many windows belong to each class. This gives us an overview of the data we will be using to train our CNN model.
print(f"X shape    : {X.shape}")
print(f"y shape    : {y.shape}")
print(f"\nClass breakdown:")
for idx, name in LABEL_NAMES.items():
    print(f"  {name:10s} ({idx}): {(y==idx).sum()} windows")

# Normalise
# Normalise per channel across all windows
# Store mean/std for each of the 6 channels for use in Arduino inference
channel_means = X.reshape(-1, NUM_CHANNELS).mean(axis=0)
channel_stds  = X.reshape(-1, NUM_CHANNELS).std(axis=0)
channel_stds  = np.where(channel_stds < 1e-6, 1.0, channel_stds)  # avoid division by zero

# We normalise the X array by subtracting the mean and dividing by the standard deviation for each channel.
X_norm = (X - channel_means) / channel_stds

# Save normalisation parameters
np.save("model/channel_means.npy", channel_means)
np.save("model/channel_stds.npy",  channel_stds)
print(f"\nChannel means: {channel_means.round(4)}")
print(f"Channel stds : {channel_stds.round(4)}")

# Split
# We split the dataset into training and testing sets using the train_test_split function from scikit-learn.
X_train, X_test, y_train, y_test = train_test_split(
    X_norm, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
# We use stratified splitting to ensure that the class distribution is preserved in both the training and testing sets. 
# The test size is set to 20% of the total dataset, and a random state is provided for reproducibility.
y_train_oh = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
y_test_oh  = tf.keras.utils.to_categorical(y_test,  NUM_CLASSES)

# We print the number of samples in the training and testing sets to confirm that the split was 
# successful and to give us an idea of how much data we have for training our CNN model.
print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")

# Model 
# 1D CNN - convolutional filters slide along the time axis (100 timesteps)
# learning to recognise temporal patterns like the impact spike and decay
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(WINDOW_SIZE, NUM_CHANNELS)),

    # First conv block - learns low-level patterns (short spikes, edges)
    tf.keras.layers.Conv1D(filters=32, kernel_size=5, activation="relu", padding="same"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling1D(pool_size=2),
    tf.keras.layers.Dropout(0.2),

    # Second conv block - learns higher-level patterns (spike + decay shape)
    tf.keras.layers.Conv1D(filters=64, kernel_size=3, activation="relu", padding="same"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling1D(pool_size=2),
    tf.keras.layers.Dropout(0.2),

    # Global average pooling - collapses time dimension
    tf.keras.layers.GlobalAveragePooling1D(),

    # Dense classifier
    # The dense layer with 64 units and ReLU activation allows the model to learn complex combinations of the features extracted by the convolutional layers.
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(NUM_CLASSES, activation="softmax")
], name="hurley_cnn")

# We compile the model using the Adam optimizer, categorical cross-entropy loss function (suitable for multi-class classification) 
# and accuracy as the evaluation metric. We then print a summary of the model architecture, which shows the layers, output shapes
# and number of parameters at each stage of the model. 
model.compile(
    # We compile the model using the Adam optimizer, which is a popular choice for training deep learning models due to its adaptive learning rate capabilities.
    optimizer="adam", 
    # We use categorical cross-entropy as the loss function since this is a multi-class classification problem and our labels are one-hot encoded.
    loss="categorical_crossentropy",
    # We specify accuracy as the metric to evaluate the performance of the model during training and testing. 
    # This will allow us to see how well the model is classifying the windows into the correct classes.
    metrics=["accuracy"]
)
# We print a summary of the model architecture, which includes the layers, output shapes, and number of parameters at each stage of the model.
model.summary()

# Train
print("\nTraining...")
# We set up an early stopping callback to monitor the validation loss during training. If the validation loss does not improve for 20 consecutive epochs, 
# training will be stopped and the best weights will be restored. This helps to prevent overfitting and ensures that we keep the best model 
# based on validation performance.
early_stop = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=20, restore_best_weights=True
)
# We train the model using the fit method, passing in the training data (X_train and y_train_oh), validation split of 20%, number of epochs, 
# batch size, and the early stopping callback. The verbose parameter is set to 1 to display progress during training. The history object returned by 
# fit will contain the training and validation loss and accuracy for each epoch, which can be used for analysis later if needed.
history = model.fit(
    X_train, y_train_oh,
    validation_split=0.2,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=[early_stop],
    verbose=1
)

# Evaluate
# After training, we evaluate the model on the test set. We use the predict method to get the predicted probabilities for each class, 
# and then take the argmax to get the predicted class labels. We then print a classification report, which includes precision, recall, 
# f1-score and support for each class, as well as overall accuracy. We also print the confusion matrix, which shows the number of true positives, 
# false positives, true negatives and false negatives for each class. This allows us to assess how well the model is performing on the unseen test 
# data and to identify any classes that may be particularly challenging for the model to classify correctly.
print(f"\n{'─'*50}")
y_pred = np.argmax(model.predict(X_test), axis=1)
print(classification_report(y_test, y_pred, target_names=list(LABEL_NAMES.values())))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Export TFLite
print("\nConverting to TFLite...")

# To quantise the model to 8-bit integers, we need to provide a representative dataset that the converter can use to calibrate the activations.
def representative_dataset():
    # We yield a few samples from the training set, reshaped to match the input shape expected by the model.
    for i in range(min(100, len(X_train))):
        # We take the i-th sample from the X_train array, convert it to float32, and reshape it to have a batch dimension of 1 
        # (i.e., shape (1, WINDOW_SIZE, NUM_CHANNELS)).
        yield [X_train[i].astype(np.float32).reshape(1, WINDOW_SIZE, NUM_CHANNELS)]

# We create a TFLiteConverter from the Keras model, set the optimization flag to default (which enables quantization),
# and provide the representative dataset function for calibration. We specify that we want to use only built-in integer operations in the converted model, 
# and that the input and output types should be float32 (the quantization will be applied to the weights and activations,
#  but the model will still accept and produce float32 values for compatibility).
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.float32
converter.inference_output_type = tf.float32

# We convert the model to TFLite format and save it to disk. We also calculate the size of the saved model in kilobytes and print this information.
tflite_model = converter.convert()
# We open a file in binary write mode and write the converted TFLite model to this file. The filename is specified by the MODEL_TFLITE variable.
with open(MODEL_TFLITE, "wb") as f:
    f.write(tflite_model)
# We calculate the size of the saved TFLite model in kilobytes by taking the length of the tflite_model byte string and dividing it by 1024. 
# We then print the filename and size of the saved model.
model_size_kb = len(tflite_model) / 1024
print(f"Saved: {MODEL_TFLITE} ({model_size_kb:.1f} KB)")

# Save model info
info = {
    "architecture":   "1D CNN",
    "input_shape":    [WINDOW_SIZE, NUM_CHANNELS],
    "channels":       ["ax", "ay", "az", "gx", "gy", "gz"],
    "num_classes":    NUM_CLASSES,
    "label_names":    LABEL_NAMES,
    "channel_means":  channel_means.tolist(),
    "channel_stds":   channel_stds.tolist(),
    "model_size_kb":  round(model_size_kb, 2)
}
# We create a dictionary called info that contains various details about the model and the dataset, including the architecture, 
# input shape, channel names, number of classes, label names, channel means and standard deviations used for normalization
# and the size of the saved model in kilobytes. We then save this information to a JSON file specified by MODEL_INFO_FILE for future reference.
with open(MODEL_INFO_FILE, "w") as f:
    json.dump(info, f, indent=2)

# We print the filename of the saved model information JSON file, and then print a final message indicating that the process is complete.
# We also suggest comparing the confusion matrix output against a feature-based approach (presumably implemented in another script) to evaluate 
# which method works better. Finally, we print the size of the feature-based model (which is not calculated here but can be found in the model/ folder) 
# and the size of the CNN model we just created for comparison.
print(f"Saved: {MODEL_INFO_FILE}")
print("\nDone! Compare confusion matrix above against feature-based approach.")
print(f"Feature-based model size: check model/ folder in ML Final")
print(f"CNN model size          : {model_size_kb:.1f} KB")
