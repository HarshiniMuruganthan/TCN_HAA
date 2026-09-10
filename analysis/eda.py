import pandas as pd

# Load dataset
file_path = r"D:\AQI_Health-Risk-System\data\raw\aqi-data.xlsx"

df = pd.read_excel(file_path)

print("\n========== FIRST 5 ROWS ==========")
print(df.head())

print("\n========== DATASET SHAPE ==========")
print(df.shape)

print("\n========== COLUMNS ==========")
print(df.columns.tolist())

print("\n========== DATA TYPES ==========")
print(df.dtypes)

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== DUPLICATE ROWS ==========")
print(df.duplicated().sum())
# ==========================================
# AQI STATISTICS
# ==========================================

print("\n========== AQI STATISTICS ==========")

print("Minimum AQI:", df["aqi"].min())
print("Maximum AQI:", df["aqi"].max())
print("Average AQI:", round(df["aqi"].mean(), 2))
print("Median AQI:", df["aqi"].median())


# ==========================================
# POLLUTANT STATISTICS
# ==========================================

pollutants = ["pm25", "pm10", "co", "so2", "no2", "o3"]

print("\n========== POLLUTANT STATISTICS ==========")

for pollutant in pollutants:
    print(
        pollutant.upper(),
        "Minimum:", df[pollutant].min(),
        "Maximum:", df[pollutant].max(),
        "Average:", round(df[pollutant].mean(), 2)
    )


# ==========================================
# AQI CATEGORY
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


df["AQI_Category"] = df["aqi"].apply(aqi_category)

print("\n========== AQI CATEGORIES ==========")

print(df["AQI_Category"].value_counts())


# ==========================================
# CORRELATION WITH AQI
# ==========================================

print("\n========== CORRELATION WITH AQI ==========")

correlation = (
    df[["aqi"] + pollutants]
    .corr()["aqi"]
    .sort_values(ascending=False)
)

print(correlation)