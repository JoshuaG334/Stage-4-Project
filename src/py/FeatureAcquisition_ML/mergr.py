import pandas as pd


# LOAD DATA
idle = pd.read_csv("imu_features_idle.csv")
walking = pd.read_csv("imu_features_walking.csv")


# ADD LABELS
idle["label"] = 0
walking["label"] = 1


# MERGE DATA
all_data = pd.concat([idle, walking], ignore_index=True)


# SAVE MERGED CSV
all_data.to_csv("imu_features_all.csv", index=False)
print("Merged CSV saved as imu_features_all.csv")
