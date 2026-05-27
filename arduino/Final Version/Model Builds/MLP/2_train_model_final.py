# Joshua Geoghegan
# Smart Hurley - Model Training (Final)
# 4 classes: idle, swing, impact, fake_hit
# cd "C:\Users\joshm\Documents\4th year modules\Project\Hurl Data\ML Final"
#..\tf_env\Scripts\Activate.ps1
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
import pickle
import json
import os

# Configuration
DATASET_FILE    = "model/dataset.csv"# Output from 1_build_dataset_final.py
MODEL_TFLITE    = "model/hurley_model.tflite"# Output TFLite model file
SCALER_FILE     = "model/scaler.pkl" # Output scaler file for normalisation parameters
MODEL_INFO_FILE = "model/model_info.json" # Output JSON file with model and dataset info (feature names, label mapping, etc.)

# Label mapping and model parameters
LABEL_NAMES  = {0: "idle", 1: "swing", 2: "impact", 3: "fake_hit"}
NUM_CLASSES  = 4 # Number of classes for classification
EPOCHS       = 150 # Maximum number of training epochs
BATCH_SIZE   = 16 # Batch size for training
TEST_SIZE    = 0.2 # Proportion of dataset to use as test set
RANDOM_STATE = 42 # Random state for reproducibility

# Create output directory if it doesn't exist
os.makedirs("model", exist_ok=True)

# Load
print("Loading dataset...")
df = pd.read_csv(DATASET_FILE)
X  = df.drop(columns=["label"]).values
y  = df["label"].values

# Print dataset summary
feature_names = list(df.drop(columns=["label"]).columns)
print(f"Features : {len(feature_names)}")
print(f"Samples  : {len(X)}")
for idx, name in LABEL_NAMES.items():
    print(f"  {name:10s}: {(y==idx).sum()} windows")

# Normalise
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler parameters for later use in Arduino code
with open(SCALER_FILE, "wb") as f:
    pickle.dump(scaler, f)

# Split into train and test sets with stratification to maintain class balance
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
# One-hot encode labels for training the neural network
y_train_oh = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
y_test_oh  = tf.keras.utils.to_categorical(y_test,  NUM_CLASSES)

# Model
model = tf.keras.Sequential([ # Simple feedforward neural network with 2 hidden layers and dropout for regularization
    tf.keras.layers.Input(shape=(len(feature_names),)), # Input layer with number of features
    tf.keras.layers.Dense(32, activation="relu"),# First hidden layer with 32 neurons and ReLU activation
    tf.keras.layers.Dropout(0.2), # Dropout layer with 20% dropout rate to prevent overfitting
    tf.keras.layers.Dense(16, activation="relu"), # Second hidden layer with 16 neurons and ReLU activation
    tf.keras.layers.Dropout(0.1), # Dropout layer with 10% dropout rate
    tf.keras.layers.Dense(NUM_CLASSES, activation="softmax") # Output layer with softmax activation for multi-class classification
], name="hurley_classifier") 

# Compile the model with Adam optimizer and categorical crossentropy loss function, and track accuracy as a metric
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
model.summary()

# Train
print("\nTraining...") 
early_stop = tf.keras.callbacks.EarlyStopping( # Early stopping callback to prevent overfitting 
                                                # by monitoring validation loss and restoring best weights
    monitor="val_loss", patience=20, restore_best_weights=True
)
# Fit the model on the training data with a validation split of 20%, 
# for a maximum of 150 epochs, and using the early stopping callback
history = model.fit(
    X_train, y_train_oh,
    validation_split=0.2,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=[early_stop],
    verbose=1
)

# Evaluate
print(f"\n{'─'*50}")
y_pred = np.argmax(model.predict(X_test), axis=1) # Predict class labels for the test set and convert from one-hot encoding to class indices
# Print classification report and confusion matrix to evaluate model performance on the test set
print(classification_report(y_test, y_pred, target_names=list(LABEL_NAMES.values()))) 
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Export TFLite
print("\nConverting to TFLite...")

# Define a representative dataset generator for quantization, which yields batches of input data 
# from the training set for calibration during quantization. 
# This helps the TFLite converter determine appropriate scaling factors for quantizing the model weights and activations to int8.
def representative_dataset():
    for i in range(min(100, len(X_train))):
        yield [X_train[i].astype(np.float32).reshape(1, -1)]

# Convert the Keras model to TFLite format with optimizations for size and latency, using the representative dataset for quantization calibration.
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.float32
converter.inference_output_type = tf.float32

# Convert the model and save to file
tflite_model = converter.convert()
with open(MODEL_TFLITE, "wb") as f:
    f.write(tflite_model)

# Print model size in KB
model_size_kb = len(tflite_model) / 1024
print(f"Saved: {MODEL_TFLITE} ({model_size_kb:.1f} KB)")

# Save model info
info = {
    "feature_names":  feature_names,
    "num_features":   len(feature_names),
    "num_classes":    NUM_CLASSES,
    "label_names":    LABEL_NAMES,
    "scaler_means":   scaler.mean_.tolist(),
    "scaler_scales":  scaler.scale_.tolist(),
    "model_size_kb":  round(model_size_kb, 2)
}
# Save the model info as a JSON file for later reference (e.g. when converting to Arduino code)
with open(MODEL_INFO_FILE, "w") as f:
    json.dump(info, f, indent=2)
# Print the path to the saved model info JSON file and a final message indicating the next step in the process
print(f"Saved: {MODEL_INFO_FILE}")
print("\nDone! Next: run 3_convert_to_arduino_final.py")
