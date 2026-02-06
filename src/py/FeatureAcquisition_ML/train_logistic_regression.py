import pandas as pd
from sklearn.linear_model import LogisticRegression


# LOAD MERGED DATA
data = pd.read_csv("imu_features_all.csv")

# Features & labels
X = data[["mag_mean"]]  # Only magnitude
y = data["label"]

# TRAIN LOGISTIC REGRESSION
model = LogisticRegression()
model.fit(X, y)

# OUTPUT MODEL PARAMETERS
weight = model.coef_[0][0]
bias = model.intercept_[0]

print("=== Logistic Regression Parameters ===")
print(f"Weight (w): {weight:.6f}")
print(f"Bias (b): {bias:.6f}")

