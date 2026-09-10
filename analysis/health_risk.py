import pandas as pd

# ==========================================
# Load prepared dataset
# ==========================================

file_path = r"D:\AQI_Health-Risk-System\data\processed\aqi_model_dataset.csv"

df = pd.read_csv(file_path)


# ==========================================
# Health Risk Function
# ==========================================

def get_health_risk(aqi):

    if aqi <= 50:
        return "Low"

    elif aqi <= 100:
        return "Moderate"

    elif aqi <= 150:
        return "High"

    elif aqi <= 200:
        return "Very High"

    else:
        return "Severe"


# ==========================================
# Health Concern Function
# ==========================================

def get_health_concern(aqi):

    if aqi <= 50:
        return "Low respiratory concern"

    elif aqi <= 100:
        return "Possible respiratory irritation"

    elif aqi <= 150:
        return "Increased respiratory risk for sensitive people"

    elif aqi <= 200:
        return "Increased risk of respiratory problems"

    else:
        return "Serious air-pollution health concern"


# ==========================================
# Apply functions
# ==========================================

df["Health_Risk"] = df["aqi"].apply(
    get_health_risk
)

df["Health_Concern"] = df["aqi"].apply(
    get_health_concern
)


# ==========================================
# Display results
# ==========================================

print("\n========== HEALTH RISK DISTRIBUTION ==========")

print(
    df["Health_Risk"].value_counts()
)


print("\n========== SAMPLE RESULTS ==========")

print(
    df[
        [
            "date",
            "city",
            "aqi",
            "AQI_Category",
            "Health_Risk",
            "Health_Concern"
        ]
    ].head(10)
)


# ==========================================
# Save
# ==========================================

output_file = r"D:\AQI_Health-Risk-System\data\processed\aqi_health_risk.csv"

df.to_csv(
    output_file,
    index=False
)

print("\n==========================================")
print("Health risk dataset saved to:")
print(output_file)
print("==========================================")