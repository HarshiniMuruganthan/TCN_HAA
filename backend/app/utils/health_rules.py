def get_health_info(aqi):
    
    if aqi <= 50:
        return {
            "category": "Good",
            "health_risk": "Low",
            "health_concern": "Air quality is generally satisfactory."
        }

    elif aqi <= 100:
        return {
            "category": "Moderate",
            "health_risk": "Moderate",
            "health_concern": "Possible respiratory irritation, especially for sensitive individuals."
        }

    elif aqi <= 150:
        return {
            "category": "Unhealthy for Sensitive Groups",
            "health_risk": "High",
            "health_concern": "Sensitive individuals may experience respiratory symptoms."
        }

    elif aqi <= 200:
        return {
            "category": "Unhealthy",
            "health_risk": "High",
            "health_concern": "Everyone may begin to experience health effects."
        }

    elif aqi <= 300:
        return {
            "category": "Very Unhealthy",
            "health_risk": "Very High",
            "health_concern": "Health alert: increased risk of health effects for everyone."
        }

    else:
        return {
            "category": "Hazardous",
            "health_risk": "Severe",
            "health_concern": "Health emergency conditions. Everyone is likely to be affected."
        }