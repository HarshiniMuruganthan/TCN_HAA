"""
live_aqi_service.py — Fetch real-time AQI data.

Data source priority:
  1. Open-Meteo Air Quality API (free, no key, genuinely current hourly data)
     https://open-meteo.com/en/docs/air-quality-api
  2. AQICN (waqi.info) — good coverage but some stations may be stale
  3. aqi.in scraper — Cloudflare-protected, often fails
  4. Mock data — last resort fallback
"""

import logging
from datetime import datetime, timezone, timedelta

import requests
import re

from backend.app.utils.config import (
    AQICN_TOKEN,
    AQICN_BASE_URL,
    CITY_STATION_MAP,
    CITY_SLUG_FALLBACK,
    USE_MOCK_DATA,
)
from backend.app.utils.validators import validate_live_data, sanitise_live_data

logger = logging.getLogger(__name__)


# ── Timeout for API requests (seconds) ───────────────────────
_REQUEST_TIMEOUT = 10


# ╔══════════════════════════════════════════════════════════════╗
# ║  MOCK DATA — used when USE_MOCK_DATA=true or token missing  ║
# ╚══════════════════════════════════════════════════════════════╝

_MOCK_DATA: dict = {
    "chennai": {
        "city": "Chennai", "aqi": 82.0,
        "pm25": 27.4, "pm10": 42.1,
        "no2": 18.3, "so2": 4.2, "co": 0.7, "o3": 32.6,
    },
    "delhi": {
        "city": "Delhi", "aqi": 156.0,
        "pm25": 89.3, "pm10": 143.2,
        "no2": 62.1, "so2": 18.5, "co": 2.3, "o3": 41.2,
    },
    "mumbai": {
        "city": "Mumbai", "aqi": 74.0,
        "pm25": 22.1, "pm10": 38.4,
        "no2": 14.8, "so2": 3.9, "co": 0.6, "o3": 28.5,
    },
    "bengaluru": {
        "city": "Bengaluru", "aqi": 68.0,
        "pm25": 19.6, "pm10": 34.8,
        "no2": 12.4, "so2": 3.1, "co": 0.5, "o3": 25.3,
    },
    "hyderabad": {
        "city": "Hyderabad", "aqi": 91.0,
        "pm25": 31.2, "pm10": 51.7,
        "no2": 22.6, "so2": 5.8, "co": 0.9, "o3": 37.4,
    },
    "coimbatore": {
        "city": "Coimbatore", "aqi": 48.0,
        "pm25": 14.3, "pm10": 26.9,
        "no2": 8.7,  "so2": 2.3, "co": 0.4, "o3": 19.8,
    },
}



# ── City coordinates for Open-Meteo API ──────────────────────
_CITY_COORDS: dict = {
    "chennai":    (13.0827, 80.2707),
    "delhi":      (28.6139, 77.2090),
    "mumbai":     (19.0760, 72.8777),
    "bengaluru":  (12.9716, 77.5946),
    "hyderabad":  (17.3850, 78.4867),
    "coimbatore": (11.0168, 76.9558),
}

# Mapping of city keys to aqi.in URLs (state and city slug)
_AQIIN_URLS: dict = {
    "chennai":    "https://www.aqi.in/dashboard/india/tamil-nadu/chennai",
    "delhi":      "https://www.aqi.in/dashboard/india/delhi",
    "mumbai":     "https://www.aqi.in/dashboard/india/maharashtra/mumbai",
    "bengaluru":  "https://www.aqi.in/dashboard/india/karnataka/bengaluru",
    "hyderabad":  "https://www.aqi.in/dashboard/india/telangana/hyderabad",
    "coimbatore": "https://www.aqi.in/dashboard/india/tamil-nadu/coimbatore",
}



def _get_mock(city_key: str) -> dict | None:
    """Return mock data for a city (with current timestamp)."""
    base = _MOCK_DATA.get(city_key.lower())
    if base is None:
        return None
    return {
        **base,
        "timestamp": datetime.now().isoformat(),
        "source": "mock",
    }



# ╔══════════════════════════════════════════════════════════════╗
# ║  OPEN-METEO AIR QUALITY API  (PRIMARY — free, no key)      ║
# ╚══════════════════════════════════════════════════════════════╝

_OPENMETEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def _fetch_from_openmeteo(city_key: str, city_display: str) -> dict | None:
    """
    Fetch live AQI from Open-Meteo Air Quality API.
    Uses the most recent completed hourly reading.
    Returns None on any error.
    """
    coords = _CITY_COORDS.get(city_key.lower())
    if not coords:
        logger.warning("No coordinates for city: %s", city_key)
        return None

    lat, lon = coords
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "hourly":       "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        "timezone":     "Asia/Kolkata",
        "forecast_days": 1,
        "past_days":    1,   # include yesterday so we always have recent data
    }

    try:
        resp = requests.get(_OPENMETEO_URL, params=params, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except requests.exceptions.Timeout:
        logger.error("Open-Meteo timed out for %s", city_key)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Open-Meteo connection error for %s", city_key)
        return None
    except Exception as exc:
        logger.error("Open-Meteo error for %s: %s", city_key, exc)
        return None

    hourly = payload.get("hourly", {})
    times   = hourly.get("time", [])
    us_aqi  = hourly.get("us_aqi", [])
    pm25    = hourly.get("pm2_5", [])
    pm10    = hourly.get("pm10", [])
    no2     = hourly.get("nitrogen_dioxide", [])
    so2     = hourly.get("sulphur_dioxide", [])
    co      = hourly.get("carbon_monoxide", [])
    o3      = hourly.get("ozone", [])

    if not times or not us_aqi:
        logger.warning("Open-Meteo returned empty data for %s", city_key)
        return None

    # ── Pick the most recent hour that has a valid AQI value ──
    now_local = datetime.now()
    best_idx = None
    best_time = None

    for i in range(len(times) - 1, -1, -1):
        if us_aqi[i] is not None:
            try:
                t = datetime.fromisoformat(times[i])
                # Only use readings up to 1 hour in the future (allow slight clock skew)
                if t <= now_local.replace(tzinfo=None) + timedelta(hours=1):
                    best_idx = i
                    best_time = t
                    break
            except Exception:
                continue

    if best_idx is None:
        logger.warning("Open-Meteo: no valid recent AQI for %s", city_key)
        return None

    def _safe(arr, idx):
        try:
            v = arr[idx]
            return float(v) if v is not None else None
        except (IndexError, TypeError, ValueError):
            return None

    aqi_val = _safe(us_aqi, best_idx)
    if aqi_val is None:
        return None

    # CO from Open-Meteo is in µg/m³; convert to mg/m³ for consistency
    co_val = _safe(co, best_idx)
    if co_val is not None:
        co_val = round(co_val / 1000, 3)

    logger.info(
        "Open-Meteo live data: city=%s aqi=%.0f pm25=%s timestamp=%s",
        city_display, aqi_val,
        _safe(pm25, best_idx),
        best_time.isoformat() if best_time else "unknown",
    )

    return {
        "city":      city_display,
        "aqi":       aqi_val,
        "pm25":      _safe(pm25, best_idx),
        "pm10":      _safe(pm10, best_idx),
        "no2":       _safe(no2,  best_idx),
        "so2":       _safe(so2,  best_idx),
        "co":        co_val,
        "o3":        _safe(o3,   best_idx),
        "timestamp": best_time.isoformat() if best_time else datetime.now().isoformat(),
        "source":    "open-meteo",
    }


# ╔══════════════════════════════════════════════════════════════╗
# ║  AQICN API CALL  (secondary)                                ║
# ╚══════════════════════════════════════════════════════════════╝

def _extract_iaqi(iaqi: dict, key: str) -> float | None:
    """Safely extract a pollutant value from AQICN's iaqi dict."""
    try:
        return float(iaqi[key]["v"])
    except (KeyError, TypeError, ValueError):
        return None


def _fetch_from_aqicn(city_key: str) -> dict | None:
    """
    Call the AQICN API for a city/station key and return a normalised dict.
    Returns None on any API or network error.
    """
    url = f"{AQICN_BASE_URL}/{city_key}/?token={AQICN_TOKEN}"
    logger.info("AQICN request: %s", url.replace(AQICN_TOKEN, "***"))

    try:
        response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("AQICN API timed out for city: %s", city_key)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("AQICN API connection error for city: %s", city_key)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("AQICN API error for %s: %s", city_key, exc)
        return None

    try:
        payload = response.json()
    except ValueError:
        logger.error("AQICN returned non-JSON response for %s", city_key)
        return None

    # ── Check API-level status ────────────────────────────────
    if payload.get("status") != "ok":
        logger.error(
            "AQICN returned status '%s' for city '%s'. Message: %s",
            payload.get("status"),
            city_key,
            payload.get("data", ""),
        )
        return None

    data = payload.get("data", {})

    # ── Parse AQI ─────────────────────────────────────────────
    raw_aqi = data.get("aqi")
    if raw_aqi == "-" or raw_aqi is None:
        logger.warning("AQICN returned no AQI value for %s", city_key)
        return None

    # ── Parse pollutants ──────────────────────────────────────
    iaqi = data.get("iaqi", {})

    # ── Parse timestamp — detect and warn on stale data ───────
    time_block = data.get("time", {})
    iso_time = time_block.get("iso")
    now_utc = datetime.now(timezone.utc)
    stale_threshold = timedelta(hours=6)

    if iso_time:
        try:
            # Parse the ISO timestamp (handles +05:30 etc.)
            from datetime import datetime as dt
            obs_time = dt.fromisoformat(iso_time)
            # Make offset-aware for comparison
            if obs_time.tzinfo is None:
                obs_time = obs_time.replace(tzinfo=timezone.utc)
            age = now_utc - obs_time.astimezone(timezone.utc)
            if age > stale_threshold:
                logger.warning(
                    "AQICN data for %s is STALE (%.1f hours old, timestamp=%s). "
                    "Using current time as timestamp.",
                    city_key, age.total_seconds() / 3600, iso_time,
                )
                iso_time = datetime.now().isoformat()
        except Exception:
            iso_time = datetime.now().isoformat()
    else:
        iso_time = datetime.now().isoformat()

    # ── Parse city name ───────────────────────────────────────
    city_block = data.get("city", {})
    city_name = city_block.get("name", city_key.title())

    logger.info(
        "AQICN live data: city=%s aqi=%s pm25=%s timestamp=%s",
        city_name, raw_aqi,
        iaqi.get("pm25", {}).get("v", "N/A"),
        iso_time,
    )

    return {
        "city":      city_name,
        "aqi":       float(raw_aqi),
        "pm25":      _extract_iaqi(iaqi, "pm25"),
        "pm10":      _extract_iaqi(iaqi, "pm10"),
        "no2":       _extract_iaqi(iaqi, "no2"),
        "so2":       _extract_iaqi(iaqi, "so2"),
        "co":        _extract_iaqi(iaqi, "co"),
        "o3":        _extract_iaqi(iaqi, "o3"),
        "timestamp": iso_time,
        "source":    "aqicn",
    }

def _fetch_from_aqiin(city_key: str) -> dict | None:
    """Fetch live AQI data from aqi.in for a given city key.
    Returns a dict with the same schema as the AQICN fetcher, or None on failure.
    """
    url = _AQIIN_URLS.get(city_key.lower())
    if not url:
        logger.error("aqi.in URL not configured for city_key: %s", city_key)
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    }
    try:
        response = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
    except Exception as exc:
        logger.error("aqi.in request failed for %s: %s", city_key, exc)
        return None

    html = response.text
    # Updated regex to robustly capture lastUpdateTime and averageArray from the embedded JSON.
    pattern = re.compile(r'\\?"lastUpdateTime\\?":\\?"([^"\\]+)\\?".*?\\?"averageArray\\?":\[([^\]]+)\]', re.DOTALL)
    match = pattern.search(html)
    if not match:
        logger.error("Failed to parse aqi.in data for %s", city_key)
        return None

    last_update = match.group(1)
    # averageArray is a comma‑separated list of numbers (as strings)
    aqi_array = [float(x) for x in match.group(2).split(',') if x.strip()]
    current_aqi = aqi_array[-1] if aqi_array else None

    # aqi.in does not provide separate pollutant values; we return only AQI.
    return {
        "city": city_key.title(),
        "aqi": current_aqi,
        "pm25": None,
        "pm10": None,
        "no2": None,
        "so2": None,
        "co": None,
        "o3": None,
        "timestamp": last_update,
        "source": "aqi.in",
    }


# ╔══════════════════════════════════════════════════════════════╗
# ║  PUBLIC INTERFACE                                           ║
# ╚══════════════════════════════════════════════════════════════╝

def get_live_aqi(city: str) -> dict | None:
    """
    Fetch real-time AQI data for a city.

    Parameters
    ----------
    city : str
        City name matching CITY_STATION_MAP keys
        e.g. "Chennai", "Delhi", "Mumbai"

    Returns
    -------
    dict  — validated, sanitised AQI data
    None  — if city is unsupported or API/validation fails

    Example return value
    --------------------
    {
        "city":      "Chennai",
        "aqi":       82.0,
        "pm25":      27.4,
        "pm10":      42.1,
        "no2":       18.3,
        "so2":       4.2,
        "co":        0.7,
        "o3":        32.6,
        "timestamp": "2026-09-10T08:30:00+05:30",
        "source":    "aqicn"
    }
    """
    # ── Resolve city slug (used for Open-Meteo coords lookup) ──
    city_title = city.strip().title()
    city_key   = CITY_STATION_MAP.get(city_title)
    if city_key is None:
        logger.warning("Unsupported city requested: %s", city)
        return None

    # city_slug is the lowercase city name used for coords / aqi.in
    city_slug = CITY_SLUG_FALLBACK.get(city_title, city_title.lower())

    # ── 1. Try Open-Meteo first (always current, no API key) ───
    raw = None
    logger.info("Fetching Open-Meteo AQI for city: %s", city_title)
    raw = _fetch_from_openmeteo(city_slug, city_title)

    # ── 2. Fallback: AQICN station ID ──────────────────────────
    if raw is None and AQICN_TOKEN and AQICN_TOKEN != "your_aqicn_token_here":
        logger.warning("Open-Meteo failed for %s — trying AQICN station %s", city, city_key)
        raw = _fetch_from_aqicn(city_key)

        # Try city slug if station ID also failed
        if raw is None:
            slug = city_slug
            if slug and slug != city_key:
                logger.warning("AQICN station ID failed — retrying with slug '%s'", slug)
                raw = _fetch_from_aqicn(slug)

    # ── 3. Fallback: aqi.in scraper ────────────────────────────
    if raw is None:
        logger.warning("AQICN failed for %s — trying aqi.in scraper", city)
        raw = _fetch_from_aqiin(city_slug)

    # ── 4. Last resort: mock data ───────────────────────────────
    if raw is None:
        logger.warning("All sources failed for %s — falling back to mock data", city)
        raw = _get_mock(city_slug)
    else:
        # Normalise fields for consistency with existing flow
        raw["station_name"] = raw.get("city")
        raw["city"] = city_title

    if raw is None:
        return None

    # ── Validate ───────────────────────────────────────────────
    is_valid, errors = validate_live_data(raw)
    if not is_valid:
        logger.error(
            "Validation failed for %s: %s", city, errors
        )
        return None

    # ── Sanitise and return ────────────────────────────────────
    return sanitise_live_data(raw)


def get_all_cities_live() -> dict[str, dict | None]:
    """
    Fetch live AQI for all supported cities.
    Used by the background scheduler.

    Returns
    -------
    dict mapping city name → live data dict (or None if failed)
    """
    results = {}
    for city in CITY_STATION_MAP.keys():
        results[city] = get_live_aqi(city)
    return results
