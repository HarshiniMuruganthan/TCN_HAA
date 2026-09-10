import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# LOAD DATA
# ==========================================

file_path = r"D:\AQI_Health-Risk-System\data\processed\aqi_health_risk.csv"

df = pd.read_csv(file_path)

df["date"] = pd.to_datetime(df["date"])


# ==========================================
# 1. AVERAGE AQI BY CITY
# ==========================================

average_aqi = (
    df.groupby("city")["aqi"]
    .mean()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10, 6))

average_aqi.plot(kind="bar")

plt.title("Average AQI by City")
plt.xlabel("City")
plt.ylabel("Average AQI")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    "data/processed/average_aqi_by_city.png"
)

plt.show()


# ==========================================
# 2. AQI TREND BY CITY
# ==========================================

plt.figure(figsize=(12, 6))

for city in df["city"].unique():

    city_data = df[df["city"] == city]

    plt.plot(
        city_data["date"],
        city_data["aqi"],
        marker="o",
        label=city
    )

plt.title("AQI Trend Across Cities")
plt.xlabel("Date")
plt.ylabel("AQI")

plt.legend()

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    "data/processed/aqi_trend.png"
)

plt.show()


# ==========================================
# 3. POLLUTANT COMPARISON
# ==========================================

pollutants = [
    "pm25",
    "pm10"
]

pollutant_average = (
    df.groupby("city")[pollutants]
    .mean()
)

pollutant_average.plot(
    kind="bar",
    figsize=(10, 6)
)

plt.title("Average PM2.5 and PM10 by City")
plt.xlabel("City")
plt.ylabel("Pollutant Level")

plt.xticks(rotation=45)

plt.legend()

plt.tight_layout()

plt.savefig(
    "data/processed/pollutant_comparison.png"
)

plt.show()


# ==========================================
# 4. AQI CATEGORY DISTRIBUTION
# ==========================================

category_counts = (
    df["AQI_Category"]
    .value_counts()
)

plt.figure(figsize=(8, 6))

category_counts.plot(
    kind="bar"
)

plt.title("AQI Category Distribution")
plt.xlabel("AQI Category")
plt.ylabel("Number of Days")

plt.xticks(rotation=30)

plt.tight_layout()

plt.savefig(
    "data/processed/aqi_category_distribution.png"
)

plt.show()


print("\n==========================================")
print("VISUALIZATION COMPLETED")
print("==========================================")

print("\nGraphs saved in:")
print("data/processed/")