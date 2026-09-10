import os
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf


# Project root directory
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)


# File paths
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

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "aqi_master.csv"
)


# Load model and scaler once
model = tf.keras.models.load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


# Same features used during TCN training
FEATURES = [
    "aqi",
    "AQI-IN",
    "pm25",
    "pm10"
]

SEQUENCE_LENGTH = 7


def predict_city_aqi(city):

    df = pd.read_csv(DATA_PATH)

    # Select city
    city_data = df[
        df["city"].str.lower() == city.lower()
    ].copy()

    if city_data.empty:
        return None

    # Convert date
    city_data["date"] = pd.to_datetime(
        city_data["date"]
    )

    # Sort by date
    city_data = city_data.sort_values("date")

    # Need at least 7 records
    if len(city_data) < SEQUENCE_LENGTH:
        return None

    # Take latest 7 records
    latest_data = city_data[
        FEATURES
    ].tail(SEQUENCE_LENGTH)

    # Convert to numpy
    values = latest_data.values.astype(float)

    # Scale using the SAME scaler used during training
    scaled_values = scaler.transform(values)

    # Reshape for TCN
    X = scaled_values.reshape(
        1,
        SEQUENCE_LENGTH,
        len(FEATURES)
    )

    # Predict
    prediction = model.predict(
        X,
        verbose=0
    )

    predicted_aqi = float(
        prediction[0][0]
    )

    return round(predicted_aqi, 2)