"""
anomaly_service.py
------------------
Detects air quality anomalies and triggers early warnings:
1. Spike Detection: Compares current reading with recent moving average.
2. Hazardous Concentration: Flags pollutants exceeding WHO / CPCB acute exposure limits.
3. Dominant Culprit: Pinpoints the specific pollutant driving the risk spike.
"""

from typing import Any


# Acute exposure thresholds for rapid warning (µg/m³ or ppm)
ACUTE_THRESHOLDS = {
    "aqi": 150.0,    # Unhealthy threshold
    "pm25": 60.0,    # CPCB 24h standard
    "pm10": 100.0,   # CPCB 24h standard
    "no2": 80.0,     # CPCB standard
    "so2": 80.0,     # CPCB standard
    "co": 4.0,       # ppm
    "o3": 100.0,     # µg/m³ 8h standard
}


def detect_anomalies(
    current_aqi: float,
    pollutants: dict[str, float | None],
    recent_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Analyze current observation for air quality spikes and health hazard warnings.

    Returns:
    --------
    dict containing:
      - is_anomaly: bool
      - severity: 'NORMAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL'
      - title: short headline
      - description: detailed advisory
      - dominant_pollutant: key of highest exceeding pollutant
      - spike_percentage: percentage rise over recent average (if history exists)
    """
    alerts = []
    exceeded_pollutants = []
    dominant_pollutant = "AQI"
    max_exceedance_ratio = 0.0

    # 1. Check pollutant-specific acute thresholds
    for key, threshold in ACUTE_THRESHOLDS.items():
        val = current_aqi if key == "aqi" else pollutants.get(key)
        if val is not None and val > 0:
            ratio = val / threshold
            if ratio > max_exceedance_ratio:
                max_exceedance_ratio = ratio
                dominant_pollutant = key.upper()

            if ratio >= 1.0:
                exceeded_pollutants.append({
                    "pollutant": key.upper(),
                    "value": val,
                    "threshold": threshold,
                    "ratio": round(ratio, 2),
                })

    # 2. Check rate of change (spike detection) if recent history is available
    spike_detected = False
    spike_pct = 0.0
    if recent_history and len(recent_history) >= 2:
        valid_past_aqi = [float(h["aqi"]) for h in recent_history if h.get("aqi") is not None]
        if valid_past_aqi:
            baseline_avg = sum(valid_past_aqi) / len(valid_past_aqi)
            if baseline_avg > 0:
                spike_pct = round(((current_aqi - baseline_avg) / baseline_avg) * 100, 1)
                if spike_pct >= 25.0:
                    spike_detected = True
                    alerts.append(
                        f"Rapid AQI surge detected: +{spike_pct}% higher than recent 24-hour average."
                    )

    # 3. Determine severity and warning messages
    if current_aqi >= 250.0 or max_exceedance_ratio >= 2.5:
        severity = "CRITICAL"
        title = "🚨 SEVERE HEALTH HAZARD ALERT"
        description = (
            f"Air quality has reached emergency hazardous levels (AQI: {current_aqi}). "
            f"Dominant threat: {dominant_pollutant}. Immediately avoid all outdoor activity and keep air purifiers on."
        )
        is_anomaly = True
    elif current_aqi >= 150.0 or spike_detected or len(exceeded_pollutants) >= 2:
        severity = "HIGH"
        title = "⚠️ ELEVATED POLLUTION EARLY WARNING"
        description = (
            f"Air pollution is significantly elevated (AQI: {current_aqi}). "
            f"Dominant pollutant: {dominant_pollutant}. Vulnerable groups and sensitive individuals must wear N95 masks."
        )
        is_anomaly = True
    elif current_aqi >= 100.0 or len(exceeded_pollutants) >= 1:
        severity = "ELEVATED"
        title = "📢 MODERATE AIR QUALITY ADVISORY"
        description = (
            f"Pollution is slightly elevated (AQI: {current_aqi}). "
            f"{dominant_pollutant} levels warrant caution for prolonged outdoor exertion."
        )
        is_anomaly = False
    else:
        severity = "NORMAL"
        title = "✅ NORMAL AIR QUALITY CONDITIONS"
        description = (
            f"Air quality is within acceptable safety parameters (AQI: {current_aqi}). "
            "Normal outdoor recreation and natural ventilation are safe."
        )
        is_anomaly = False

    return {
        "is_anomaly": is_anomaly,
        "severity": severity,
        "title": title,
        "description": description,
        "dominant_pollutant": dominant_pollutant,
        "spike_detected": spike_detected,
        "spike_percentage": spike_pct,
        "exceeded_pollutants": exceeded_pollutants,
    }
