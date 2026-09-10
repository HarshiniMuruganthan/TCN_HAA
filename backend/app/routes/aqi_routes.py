from fastapi import APIRouter
import pandas as pd
import os

from backend.app.utils.health_rules import get_health_info
from backend.app.services.prediction_service import predict_city_aqi

router = APIRouter(prefix="/api", tags=["AQI"])


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "aqi_master.csv"
)


@router.get("/cities")
def get_cities():

    df = pd.read_csv(DATA_PATH)

    cities = sorted(df["city"].unique().tolist())

    return {
        "cities": cities
    }
@router.get("/aqi/{city}")
def get_city_aqi(city: str):

    df = pd.read_csv(DATA_PATH)

    city_data = df[df["city"].str.lower() == city.lower()]

    if city_data.empty:
        return {
            "error": "City not found"
        }

    city_data["date"] = pd.to_datetime(city_data["date"])

    latest = city_data.sort_values("date").iloc[-1]

    aqi = float(latest["aqi"])

    health_info = get_health_info(aqi)

    return {
        "city": latest["city"],
        "date": str(latest["date"]),
        "aqi": aqi,
        "AQI-IN": float(latest["AQI-IN"]),
        "pm25": float(latest["pm25"]),
        "pm10": float(latest["pm10"]),
        "aqi_category": health_info["category"],
        "health_risk": health_info["health_risk"],
        "health_concern": health_info["health_concern"]
    }
@router.get("/prediction/{city}")
def get_prediction(city: str):

    prediction = predict_city_aqi(city)

    if prediction is None:
        return {
            "error": "Unable to generate prediction for this city"
        }

    health_info = get_health_info(prediction)

    return {
        "city": city,
        "predicted_aqi": prediction,
        "aqi_category": health_info["category"],
        "health_risk": health_info["health_risk"],
        "health_concern": health_info["health_concern"]
    }
@router.get("/dashboard/{city}")
def get_dashboard(city: str):

    df = pd.read_csv(DATA_PATH)

    city_data = df[
        df["city"].str.lower() == city.lower()
    ].copy()

    if city_data.empty:
        return {
            "error": "City not found"
        }

    city_data["date"] = pd.to_datetime(city_data["date"])
    city_data = city_data.sort_values("date")

    latest = city_data.iloc[-1]

    current_aqi = float(latest["aqi"])

    current_health = get_health_info(current_aqi)

    predicted_aqi = predict_city_aqi(city)

    predicted_health = get_health_info(predicted_aqi)

    return {
        "city": latest["city"],

        "current": {
            "date": str(latest["date"]),
            "aqi": current_aqi,
            "AQI-IN": float(latest["AQI-IN"]),
            "pm25": float(latest["pm25"]),
            "pm10": float(latest["pm10"]),
            "category": current_health["category"],
            "health_risk": current_health["health_risk"],
            "health_concern": current_health["health_concern"]
        },

        "prediction": {
            "predicted_aqi": predicted_aqi,
            "category": predicted_health["category"],
            "health_risk": predicted_health["health_risk"],
            "health_concern": predicted_health["health_concern"]
        }
    }