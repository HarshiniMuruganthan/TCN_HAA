import pandas as pd
import os

# ==========================================
# 1. Load dataset
# ==========================================

input_file = r"D:\AQI_Health-Risk-System\data\processed\aqi_health_risk.csv"

df = pd.read_csv(input_file)

print("\n========== ORIGINAL DATA ==========")
print(df.shape)


# ==========================================
# 2. Convert date
# ==========================================

df["date"] = pd.to_datetime(df["date"])


# ==========================================
# 3. Create date features
# ==========================================

df["day"] = df["date"].dt.day
df["month"] = df["date"].dt.month
df["day_of_week"] = df["date"].dt.dayofweek


# ==========================================
# 4. Select ML features
# ==========================================

features = [
    "city",
    "AQI-IN",
    "pm25",
    "pm10",
    "day",
    "month",
    "day_of_week"
]

target = "Health_Risk"


X = df[features].copy()
y = df[target].copy()


# ==========================================
# 5. Display information
# ==========================================

print("\n========== FEATURES ==========")

print(X.head())

print("\n========== TARGET ==========")

print(y.value_counts())


# ==========================================
# 6. Save ML dataset
# ==========================================

ml_data = X.copy()

ml_data["Health_Risk"] = y

output_file = r"D:\AQI_Health-Risk-System\data\processed\ml_dataset.csv"

ml_data.to_csv(
    output_file,
    index=False
)


print("\n==========================================")
print("ML DATASET CREATED")
print("==========================================")

print("Rows:", len(ml_data))
print("Columns:", len(ml_data.columns))

print("\nSaved to:")
print(output_file)