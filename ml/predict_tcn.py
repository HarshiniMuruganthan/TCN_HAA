import os
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\AQI_Health-Risk-System"

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "tcn_aqi_model.keras"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "data",
    "tcn_scaler.pkl"
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "aqi_master.csv"
)


# ============================================================
# SETTINGS
# ============================================================

SEQUENCE_LENGTH = 7

FEATURES = [
    "aqi",
    "AQI-IN",
    "pm25",
    "pm10"
]


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 60)
print("LOADING TCN MODEL")
print("=" * 60)

model = tf.keras.models.load_model(
    MODEL_PATH
)

print("TCN model loaded successfully.")


# ============================================================
# LOAD SCALER
# ============================================================

scaler = joblib.load(
    SCALER_PATH
)

print("TCN scaler loaded successfully.")


# ============================================================
# LOAD DATA
# ============================================================

print("\n" + "=" * 60)
print("LOADING AQI DATA")
print("=" * 60)

df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(
    df["date"]
)

df = df.sort_values(
    ["city", "date"]
).reset_index(drop=True)

print("Rows:", len(df))
print("Cities:", df["city"].unique())


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
# PREDICTION FUNCTION
# ============================================================

def predict_next_day(city):

    print("\n" + "=" * 60)
    print(f"PREDICTING NEXT-DAY AQI FOR {city}")
    print("=" * 60)

    city_df = df[
        df["city"].str.lower()
        == city.lower()
    ].copy()

    city_df = city_df.sort_values(
        "date"
    ).reset_index(drop=True)


    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    if len(city_df) < SEQUENCE_LENGTH:

        raise ValueError(
            f"Not enough data for {city}. "
            f"Need at least {SEQUENCE_LENGTH} days."
        )


    # --------------------------------------------------------
    # GET LAST 7 DAYS
    # --------------------------------------------------------

    last_7 = city_df.tail(
        SEQUENCE_LENGTH
    ).copy()

    print("\nLast 7 days used:")

    print(
        last_7[
            ["date", "aqi", "AQI-IN", "pm25", "pm10"]
        ].to_string(index=False)
    )


    # --------------------------------------------------------
    # CREATE INPUT SEQUENCE
    # --------------------------------------------------------

    sequence = last_7[
        FEATURES
    ].values.astype(
        np.float32
    )


    # --------------------------------------------------------
    # SCALE
    # --------------------------------------------------------

    sequence_scaled = scaler.transform(
        sequence
    )


    # --------------------------------------------------------
    # RESHAPE FOR TCN
    # --------------------------------------------------------

    X_input = sequence_scaled.reshape(
        1,
        SEQUENCE_LENGTH,
        len(FEATURES)
    )


    print("\nInput shape:", X_input.shape)


    # --------------------------------------------------------
    # PREDICT
    # --------------------------------------------------------

    prediction = model.predict(
        X_input,
        verbose=0
    )


    predicted_aqi = float(
        prediction[0][0]
    )


    # --------------------------------------------------------
    # AQI CATEGORY
    # --------------------------------------------------------

    if predicted_aqi <= 50:

        category = "Good"

        health_risk = "Low"

        health_concern = (
            "Air quality is generally satisfactory."
        )

    elif predicted_aqi <= 100:

        category = "Moderate"

        health_risk = "Moderate"

        health_concern = (
            "Possible respiratory irritation, "
            "especially for sensitive individuals."
        )

    elif predicted_aqi <= 150:

        category = (
            "Unhealthy for Sensitive Groups"
        )

        health_risk = "High"

        health_concern = (
            "Sensitive individuals may experience "
            "respiratory symptoms."
        )

    elif predicted_aqi <= 200:

        category = "Unhealthy"

        health_risk = "High"

        health_concern = (
            "Everyone may begin to experience "
            "health effects."
        )

    elif predicted_aqi <= 300:

        category = "Very Unhealthy"

        health_risk = "Very High"

        health_concern = (
            "Health alert: increased risk of "
            "respiratory and cardiovascular effects."
        )

    else:

        category = "Hazardous"

        health_risk = "Severe"

        health_concern = (
            "Serious health effects are possible "
            "for the entire population."
        )


    # ========================================================
    # RESULT
    # ========================================================

    print("\n" + "=" * 60)
    print("TCN PREDICTION RESULT")
    print("=" * 60)

    print(
        f"City              : {city}"
    )

    print(
        f"Last Recorded AQI : "
        f"{last_7.iloc[-1]['aqi']:.2f}"
    )

    print(
        f"Predicted AQI     : "
        f"{predicted_aqi:.2f}"
    )

    print(
        f"AQI Category      : "
        f"{category}"
    )

    print(
        f"Health Risk       : "
        f"{health_risk}"
    )

    print(
        f"Health Concern    : "
        f"{health_concern}"
    )

    print("=" * 60)


    return {
        "city": city,
        "predicted_aqi": predicted_aqi,
        "aqi_category": category,
        "health_risk": health_risk,
        "health_concern": health_concern
    }


# ============================================================
# TEST PREDICTION
# ============================================================

if __name__ == "__main__":

    cities = [
        "Bengaluru",
        "Chennai",
        "Coimbatore",
        "Delhi",
        "Hyderabad",
        "Mumbai"
    ]

    results = []

    for city in cities:

        result = predict_next_day(city)

        results.append(result)


    # ========================================================
    # SAVE PREDICTIONS
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    output_file = os.path.join(
        BASE_DIR,
        "data",
        "processed",
        "tcn_predictions.csv"
    )

    results_df.to_csv(
        output_file,
        index=False
    )

    print("\n" + "=" * 60)
    print("ALL TCN PREDICTIONS COMPLETED")
    print("=" * 60)

    print(
        results_df.to_string(
            index=False
        )
    )

    print("\nSaved to:")
    print(output_file)