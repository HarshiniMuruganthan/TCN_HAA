"""
exposure_simulator_service.py — Engine for Personalized Exposure Risk Simulation.

Calculates individual physiological pollution exposure dose based on:
1. Live Open-Meteo AQI + Pollutant metrics (PM2.5, PM10, NO2, SO2, CO, O3)
2. Specific Disease Vulnerability Profile:
   - Asthma (Airway Hyperresponsiveness)
   - Bronchitis (Airway Mucosal Inflammation)
   - Ischemic Heart Disease (IHD)* (Cardiovascular / Plaque Risk)
   - COPD (Chronic Obstructive Pulmonary Disease)
   - General Population (Baseline)
3. Physical Activity Level (Walking, Running, Cycling, Outdoor Work, Travelling)
4. Exposure Duration (15 min, 30 min, 1 hour, 2 hours, 4 hours)
"""

import math

BREATHING_MULTIPLIERS = {
    "walking": 1.2,
    "running": 3.5,
    "cycling": 2.8,
    "outdoor_work": 2.2,
    "travelling": 1.0,
}

VULNERABILITY_MULTIPLIERS = {
    "asthma": 2.2,
    "bronchitis": 1.9,
    "ihd": 2.4,
    "copd": 2.3,
    "general": 1.0,
}

PROFILE_NAMES = {
    "asthma": "Asthma (Airway Hyperresponsiveness)",
    "bronchitis": "Bronchitis (Airway Mucosal Inflammation)",
    "ihd": "Ischemic Heart Disease (IHD)* (Cardiovascular / Plaque Risk)",
    "copd": "COPD (Chronic Obstructive Pulmonary Disease)",
    "general": "General Population (Baseline)",
}

ACTIVITY_NAMES = {
    "walking": "Outdoor Walking",
    "running": "Outdoor Running / Cardio",
    "cycling": "Cycling / Biking",
    "outdoor_work": "Heavy Outdoor Manual Work",
    "travelling": "Commuting / Travelling",
}


def calculate_exposure_risk(
    current_aqi: float,
    pollutants: dict,
    profile: str = "asthma",
    activity: str = "running",
    duration_minutes: int = 60,
) -> dict:
    """
    Calculate personalized exposure risk score, advisability,
    recommended maximum outdoor time, dominant culprit pollutant, and rationale.
    """
    profile = profile.lower() if profile in VULNERABILITY_MULTIPLIERS else "asthma"
    activity = activity.lower() if activity in BREATHING_MULTIPLIERS else "running"
    duration_minutes = int(duration_minutes) if duration_minutes in [15, 30, 60, 120, 240] else 60

    breathing_mult = BREATHING_MULTIPLIERS[activity]
    vuln_mult = VULNERABILITY_MULTIPLIERS[profile]
    duration_hours = duration_minutes / 60.0

    # Determine dominant culprit pollutant
    pm25_val = float(pollutants.get("pm25") or 0.0)
    o3_val = float(pollutants.get("o3") or 0.0)
    pm10_val = float(pollutants.get("pm10") or 0.0)
    so2_val = float(pollutants.get("so2") or 0.0)
    co_val = float(pollutants.get("co") or 0.0)

    pm25_ratio = pm25_val / 60.0
    o3_ratio = o3_val / 100.0
    pm10_ratio = pm10_val / 100.0
    so2_ratio = so2_val / 80.0

    if profile == "ihd" and pm25_ratio > 0.4:
        dominant_culprit = "PM2.5 (Ultrafine Translocating Particulates)"
    elif profile == "bronchitis" and (pm10_ratio > 0.5 or so2_ratio > 0.4):
        dominant_culprit = "PM10 & SO₂ (Bronchial Mucosa Irritants)"
    elif profile == "asthma" and o3_ratio > 0.5:
        dominant_culprit = "O₃ (Ozone Bronchospasm Trigger)"
    elif o3_ratio >= pm25_ratio and o3_ratio >= pm10_ratio and o3_ratio > 0.4:
        dominant_culprit = "O₃ (Ground-Level Ozone)"
    elif pm25_ratio >= o3_ratio and pm25_ratio >= pm10_ratio and pm25_ratio > 0.4:
        dominant_culprit = "PM2.5 (Fine Particulates)"
    elif pm10_ratio > 0.5:
        dominant_culprit = "PM10 (Coarse Inhalable Dust)"
    else:
        dominant_culprit = "Ambient Particulate Mixture"

    # Effective Inhaled Dose Formula
    raw_dose = (current_aqi / 100.0) * breathing_mult * vuln_mult * (duration_hours ** 0.85) * 45.0
    risk_score = round(min(100.0, max(5.0, raw_dose)), 1)

    # Risk level categorization
    if risk_score <= 25.0:
        level_label = "Low Exposure Risk"
        level_icon = "🟢"
        color = "#10b981"
        advisable_status = "Advisable"
        max_duration = "Up to 4 hours"
        recommendation = f"{ACTIVITY_NAMES[activity]} is safe. Maintain normal routine while keeping standard medication on hand."
    elif risk_score <= 50.0:
        level_label = "Moderate Exposure Risk"
        level_icon = "🟡"
        color = "#f59e0b"
        advisable_status = "Caution Advised"
        max_duration = "Up to 45 minutes"
        recommendation = f"Limit intense {activity} near busy roads. Take frequent breaks and stay well hydrated."
    elif risk_score <= 75.0:
        level_label = "High Exposure Risk"
        level_icon = "🔴"
        color = "#ef4444"
        advisable_status = "Not Recommended"
        max_duration = "Max 15 - 20 minutes"
        recommendation = f"Avoid outdoor {activity}. Prone to acute symptoms; exercise indoors in a HEPA air-filtered area."
    else:
        level_label = "Severe Hazardous Exposure"
        level_icon = "🚨"
        color = "#e11d48"
        advisable_status = "Strictly Avoid"
        max_duration = "0 minutes (Stay Indoors)"
        recommendation = f"Strictly cancel outdoor {activity}. High risk of medical emergency; remain in sealed room with HEPA filtration."

    # Specific pathophysiological rationale factors
    why_factors = []
    if current_aqi >= 100:
        why_factors.append(f"Current AQI ({round(current_aqi)}) exceeds clean air threshold.")
    else:
        why_factors.append(f"Current AQI is {round(current_aqi)}.")

    why_factors.append(f"Dominant culprit: {dominant_culprit}.")

    if profile == "asthma":
        why_factors.append("Asthma diagnosis: High susceptibility to sudden airway hyperreactivity & bronchospasm (2.2x risk multiplier).")
    elif profile == "bronchitis":
        why_factors.append("Bronchitis diagnosis: Bronchial mucosa easily irritated by dust & sulfur gases, producing phlegm and cough spasms (1.9x risk multiplier).")
    elif profile == "ihd":
        why_factors.append("Ischemic Heart Disease (IHD)* diagnosis: Inhaled PM2.5 triggers systemic vascular inflammation & myocardial ischemia (2.4x risk multiplier).")
    elif profile == "copd":
        why_factors.append("COPD diagnosis: Alveolar destruction and irreversible airflow limitation make lungs prone to severe flare-ups (2.3x risk multiplier).")
    else:
        why_factors.append("General population baseline physiological response.")

    if breathing_mult > 1.5:
        why_factors.append(f"{ACTIVITY_NAMES[activity]} increases hyperventilation & breathing volume by {breathing_mult}x.")

    why_factors.append(f"Exposure duration of {duration_minutes} minutes accumulates inhaled particulate dose.")

    return {
        "profile": profile,
        "profile_label": PROFILE_NAMES[profile],
        "activity": activity,
        "activity_label": ACTIVITY_NAMES[activity],
        "duration_minutes": duration_minutes,
        "risk_score": risk_score,
        "exposure_level": level_label,
        "level_icon": level_icon,
        "color": color,
        "advisable_status": advisable_status,
        "max_recommended_duration": max_duration,
        "dominant_pollutant": dominant_culprit,
        "why_factors": why_factors,
        "recommendation": recommendation,
        "multipliers": {
            "breathing_multiplier": breathing_mult,
            "vulnerability_multiplier": vuln_mult,
        },
    }
