import pandas as pd
import os

# ==========================================
# 1. Load master dataset
# ==========================================

input_file = r"D:\AQI_Health-Risk-System\data\processed\aqi_master.csv"

df = pd.read_csv(input_file)

print("\n========== ORIGINAL DATA ==========")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ==========================================
# 2. Convert date
# ==========================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)


# ==========================================
# 3. Select common features
# ==========================================

features = [
    "date",
    "city",
    "AQI-IN",
    "pm25",
    "pm10",
    "aqi"
]

df_model = df[features].copy()


# ==========================================
# 4. Remove rows with missing values
# ==========================================

df_model = df_model.dropna()


# ==========================================
# 5. Create AQI category
# ==========================================

def aqi_category(aqi):

    if aqi <= 50:
        return "Good"

    elif aqi <= 100:
        return "Moderate"

    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"

    elif aqi <= 200:
        return "Unhealthy"

    elif aqi <= 300:
        return "Very Unhealthy"

    else:
        return "Hazardous"


df_model["AQI_Category"] = df_model["aqi"].apply(
    aqi_category
)


# ==========================================
# 6. Display category distribution
# ==========================================

print("\n========== AQI CATEGORY DISTRIBUTION ==========")

print(
    df_model["AQI_Category"].value_counts()
)


# ==========================================
# 7. Display city statistics
# ==========================================

print("\n========== CITY AQI STATISTICS ==========")

city_stats = df_model.groupby("city")["aqi"].agg(
    ["min", "max", "mean"]
)

print(
    city_stats.round(2)
)


# ==========================================
# 8. Display pollutant statistics
# ==========================================

print("\n========== POLLUTANT STATISTICS ==========")

print(
    df_model[
        ["AQI-IN", "pm25", "pm10"]
    ].describe().round(2)
)


# ==========================================
# 9. Save analysis dataset
# ==========================================

output_folder = r"D:\AQI_Health-Risk-System\data\processed"

os.makedirs(
    output_folder,
    exist_ok=True
)

output_file = os.path.join(
    output_folder,
    "aqi_model_dataset.csv"
)

df_model.to_csv(
    output_file,
    index=False
)


# ==========================================
# 10. Final result
# ==========================================

print("\n========== FINAL DATASET ==========")

print("Rows:", len(df_model))

print("Columns:", len(df_model.columns))

print("\nColumns:")
print(df_model.columns.tolist())

print("\nSaved to:")
print(output_file)