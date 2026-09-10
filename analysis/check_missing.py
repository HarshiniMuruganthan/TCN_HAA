import pandas as pd

# Load master dataset
file_path = r"D:\AQI_Health-Risk-System\data\processed\aqi_master.csv"

df = pd.read_csv(file_path)

print("\n========== MISSING VALUES BY CITY ==========")

missing_by_city = df.groupby("city").apply(
    lambda x: x.isnull().sum(),
    include_groups=False
)

print(missing_by_city)


print("\n========== MISSING VALUES SUMMARY ==========")

for city in df["city"].unique():

    city_data = df[df["city"] == city]

    print("\n", city)
    print("-" * 30)

    print(city_data.isnull().sum())


print("\n========== DATA AVAILABLE BY CITY ==========")

for city in df["city"].unique():

    city_data = df[df["city"] == city]

    print(
        city,
        "->",
        len(city_data),
        "rows"
    )

    for column in [
        "aqi",
        "AQI-IN",
        "pm25",
        "pm10",
        "co",
        "so2",
        "no2",
        "o3"
    ]:

        available = city_data[column].notna().sum()

        print(
            f"   {column}: {available}/{len(city_data)} available"
        )