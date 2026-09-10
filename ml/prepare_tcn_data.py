import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib

# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\AQI_Health-Risk-System"

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "aqi_master.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "data"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

SEQUENCE_LENGTH = 7

# We use AQI itself + available pollutant information
FEATURES = [
    "aqi",
    "AQI-IN",
    "pm25",
    "pm10"
]

TARGET = "aqi"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING AQI DATA")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

df["date"] = pd.to_datetime(df["date"])

df = df.sort_values(
    ["city", "date"]
).reset_index(drop=True)

print("Rows:", len(df))
print("Cities:", df["city"].nunique())

print("\nCities:")
print(df["city"].unique())


# ============================================================
# CHECK FEATURES
# ============================================================

print("\n" + "=" * 60)
print("FEATURES")
print("=" * 60)

print(FEATURES)

print("\nMissing values:")

for feature in FEATURES:
    print(
        f"{feature}:",
        df[feature].isna().sum()
    )


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

for feature in FEATURES:

    df[feature] = (
        df.groupby("city")[feature]
        .transform(
            lambda x: x.interpolate(
                method="linear",
                limit_direction="both"
            )
        )
    )


# ============================================================
# CREATE SEQUENCES
# ============================================================

print("\n" + "=" * 60)
print("CREATING 7-DAY SEQUENCES")
print("=" * 60)

X = []
y = []
sequence_info = []

for city, city_df in df.groupby("city"):

    city_df = city_df.sort_values("date").reset_index(drop=True)

    feature_values = city_df[FEATURES].values
    target_values = city_df[TARGET].values

    for i in range(
        SEQUENCE_LENGTH,
        len(city_df)
    ):

        # Previous 7 days
        sequence = feature_values[
            i - SEQUENCE_LENGTH:i
        ]

        # Next-day AQI
        target = target_values[i]

        X.append(sequence)
        y.append(target)

        sequence_info.append({
            "city": city,
            "target_date": city_df.loc[i, "date"]
        })


X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.float32)

sequence_info = pd.DataFrame(sequence_info)


print("X shape:", X.shape)
print("y shape:", y.shape)
print("Total sequences:", len(X))


# ============================================================
# CHRONOLOGICAL TRAIN / TEST SPLIT
# ============================================================

print("\n" + "=" * 60)
print("CHRONOLOGICAL TRAIN / TEST SPLIT")
print("=" * 60)

train_indices = []
test_indices = []

# Split separately for each city
for city in sequence_info["city"].unique():

    city_indices = sequence_info[
        sequence_info["city"] == city
    ].index.to_numpy()

    split_point = int(
        len(city_indices) * 0.8
    )

    train_indices.extend(
        city_indices[:split_point]
    )

    test_indices.extend(
        city_indices[split_point:]
    )


train_indices = np.array(train_indices)
test_indices = np.array(test_indices)


X_train = X[train_indices]
y_train = y[train_indices]

X_test = X[test_indices]
y_test = y[test_indices]

sequence_train_info = sequence_info.iloc[
    train_indices
].reset_index(drop=True)

sequence_test_info = sequence_info.iloc[
    test_indices
].reset_index(drop=True)


print("X_train:", X_train.shape)
print("y_train:", y_train.shape)

print("X_test :", X_test.shape)
print("y_test :", y_test.shape)


# ============================================================
# SCALE USING TRAINING DATA ONLY
# ============================================================

print("\n" + "=" * 60)
print("SCALING DATA")
print("=" * 60)

scaler = MinMaxScaler()

# Reshape training data
X_train_2d = X_train.reshape(
    -1,
    X_train.shape[-1]
)

X_test_2d = X_test.reshape(
    -1,
    X_test.shape[-1]
)


# Fit ONLY on training data
scaler.fit(X_train_2d)


X_train_scaled = scaler.transform(
    X_train_2d
).reshape(X_train.shape)


X_test_scaled = scaler.transform(
    X_test_2d
).reshape(X_test.shape)


# ============================================================
# SAVE DATA
# ============================================================

np.save(
    os.path.join(
        OUTPUT_DIR,
        "X_train.npy"
    ),
    X_train_scaled
)

np.save(
    os.path.join(
        OUTPUT_DIR,
        "X_test.npy"
    ),
    X_test_scaled
)

np.save(
    os.path.join(
        OUTPUT_DIR,
        "y_train.npy"
    ),
    y_train
)

np.save(
    os.path.join(
        OUTPUT_DIR,
        "y_test.npy"
    ),
    y_test
)


# ============================================================
# SAVE SCALER
# ============================================================

SCALER_PATH = os.path.join(
    OUTPUT_DIR,
    "tcn_scaler.pkl"
)

joblib.dump(
    scaler,
    SCALER_PATH
)


# ============================================================
# SAVE SEQUENCE INFORMATION
# ============================================================

sequence_train_info.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "sequence_train_info.csv"
    ),
    index=False
)

sequence_test_info.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "sequence_test_info.csv"
    ),
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 60)
print("IMPROVED TCN DATA PREPARATION COMPLETED")
print("=" * 60)

print("Features:", FEATURES)
print("Sequence length:", SEQUENCE_LENGTH)

print("\nTraining:")
print("X_train:", X_train_scaled.shape)
print("y_train:", y_train.shape)

print("\nTesting:")
print("X_test:", X_test_scaled.shape)
print("y_test:", y_test.shape)

print("\nSaved:")
print("X_train.npy")
print("X_test.npy")
print("y_train.npy")
print("y_test.npy")
print("tcn_scaler.pkl")
print("sequence_train_info.csv")
print("sequence_test_info.csv")

print("=" * 60)