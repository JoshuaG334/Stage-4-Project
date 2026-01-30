# Joshua Geoghegan
# 27/01/2026
# train_model.py
# Loads accelerometer features, trains a KNN classifier, and evaluates performance

# Import pandas for handling CSVs and dataFrames
import pandas as pd

# Import train_test_split to split data into training and testing sets
from sklearn.model_selection import train_test_split

# Import KNeighborsClassifier for machine learning classification
from sklearn.neighbors import KNeighborsClassifier

# Import accuracy_score and confusion_matrix for evaluating the model
from sklearn.metrics import accuracy_score, confusion_matrix


# Load feature datasets

# Read walking and idle features CSVs into dataFrames
walking = pd.read_csv("walking_features.csv")
idle = pd.read_csv("idle_features.csv")

# Print number of rows for sanity check
print("Walking rows:", len(walking))
print("Idle rows:", len(idle))

# Combine walking and idle dataFrames into one dataset
data = pd.concat([walking, idle], ignore_index=True)


# Prepare features (X) and labels (y)

# X contains the numeric feature columns used for training
X = data[['mean', 'std', 'max', 'min', 'rms']]

# y contains the activity labels ('walking' or 'idle')
y = data['label']


# Split data into training and test sets

# 80% training, 20% testing; random_state ensures reproducibility
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Train the KNN model

# Initialize KNN classifier with 3 neighbors
model = KNeighborsClassifier(n_neighbors=3)

# Train the model on the training data
model.fit(X_train, y_train)


# Evaluate the model
# Predict labels on the test set
y_pred = model.predict(X_test)

# Compute model accuracy
accuracy = accuracy_score(y_test, y_pred)

# Compute confusion matrix to inspect classification performance
conf_matrix = confusion_matrix(y_test, y_pred)

# Print results
print("Model Accuracy:", accuracy)
print("Confusion Matrix:")
print(conf_matrix)
