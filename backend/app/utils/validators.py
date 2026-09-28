"""
validators.py — Validate and sanitise live API responses
before they are used or stored.
"""

from datetime import datetime


# ── Acceptable pollutant ranges (µg/m³ or ppm) ────────────────
_RANGES = {
    "aqi":  (0, 500),
    "pm25": (0, 500),
    "pm10": (0, 600),
    "no2":  (0, 2000),
    "so2":  (0, 1000),
    "co":   (0, 50),
    "o3":   (0, 500),
}


def _is_in_range(value: float, key: str) -> bool:
    """Return True if value is within the expected range for key."""
    low, high = _RANGES.get(key, (None, None))
    if low is None:
        return True
    return low <= value <= high


def validate_live_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validate a parsed live AQI data dict.

    Returns
    -------
    (is_valid: bool, errors: list[str])
    """
    errors: list[str] = []

    # ── Required fields ──────────────────────────────────────
    required = ["city", "aqi", "timestamp"]
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return False, errors

    # ── AQI must be numeric ──────────────────────────────────
    try:
        aqi_val = float(data["aqi"])
    except (TypeError, ValueError):
        errors.append(f"AQI is not numeric: {data['aqi']}")
        return False, errors

    if not _is_in_range(aqi_val, "aqi"):
        errors.append(
            f"AQI value {aqi_val} is outside acceptable range 0–500"
        )

    # ── Pollutant range checks (optional fields) ─────────────
    optional_pollutants = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    for key in optional_pollutants:
        val = data.get(key)
        if val is not None:
            try:
                fval = float(val)
                if not _is_in_range(fval, key):
                    errors.append(
                        f"{key.upper()} value {fval} is outside "
                        f"acceptable range {_RANGES[key]}"
                    )
            except (TypeError, ValueError):
                errors.append(
                    f"{key.upper()} is not numeric: {val}"
                )

    # ── Timestamp must be parseable ──────────────────────────
    ts = data.get("timestamp")
    if ts:
        try:
            datetime.fromisoformat(str(ts))
        except ValueError:
            errors.append(f"Invalid timestamp format: {ts}")

    is_valid = len(errors) == 0
    return is_valid, errors


def sanitise_live_data(data: dict) -> dict:
    """
    Return a clean version of the raw live data dict:
    - Round floats to 2 decimal places
    - Replace None pollutants with 0.0
    - Ensure city is title-cased
    """
    pollutants = ["pm25", "pm10", "no2", "so2", "co", "o3"]

    clean = {
        "city":      data.get("city", "").strip().title(),
        "aqi":       round(float(data["aqi"]), 2),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "source":    data.get("source", "aqicn"),
    }

    for key in pollutants:
        raw = data.get(key)
        try:
            clean[key] = round(float(raw), 2) if raw is not None else None
        except (TypeError, ValueError):
            clean[key] = None

    return clean
