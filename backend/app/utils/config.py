"""
config.py — Centralised environment variable management.
All other modules import from here — never read os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)
load_dotenv(os.path.join(_BASE_DIR, ".env"))


# ── AQICN API ────────────────────────────────────────────────
AQICN_TOKEN: str = os.getenv("AQICN_TOKEN", "")
AQICN_BASE_URL: str = "https://api.waqi.info/feed"

# ── App settings ─────────────────────────────────────────────
COLLECTION_INTERVAL_MINUTES: int = int(
    os.getenv("COLLECTION_INTERVAL_MINUTES", "60")
)

USE_MOCK_DATA: bool = (
    os.getenv("USE_MOCK_DATA", "false").lower() == "true"
)

# ── Project paths ─────────────────────────────────────────────
BASE_DIR: str = _BASE_DIR
DATA_DIR: str = os.path.join(BASE_DIR, "data", "processed")
ML_DIR: str = os.path.join(BASE_DIR, "ml")

# ── Supported cities with AQICN station IDs ─────────────────
# Key  = city name used across the project
# Value = AQICN station ID (e.g. @7023) for live data.
# These IDs resolve to specific monitoring stations that report
# current readings. Use `@idx` format for the feed endpoint:
#   https://api.waqi.info/feed/@{idx}/?token=...
# Fallback slugs are used if station ID returns no data.
CITY_STATION_MAP: dict = {
    "Chennai":    "@7023",    # Chennai US Consulate (most reliable active station)
    "Delhi":      "@10111",   # Major Dhyan Chand National Stadium, Delhi
    "Mumbai":     "@3160",    # Mumbai MPCB Bandra
    "Bengaluru":  "@7021",    # Bengaluru Peenya
    "Hyderabad":  "@5892",    # Hyderabad TSPCB Bollaram
    "Coimbatore": "@13563",   # Coimbatore TNPCB
}

# Fallback city slugs if station ID fetch fails
CITY_SLUG_FALLBACK: dict = {
    "Chennai":    "chennai",
    "Delhi":      "delhi",
    "Mumbai":     "mumbai",
    "Bengaluru":  "bengaluru",
    "Hyderabad":  "hyderabad",
    "Coimbatore": "coimbatore",
}


def validate_config() -> list[str]:
    """Return a list of configuration warnings."""
    warnings = []
    if not AQICN_TOKEN or AQICN_TOKEN == "your_aqicn_token_here":
        warnings.append(
            "AQICN_TOKEN is not set. "
            "Get a free token at https://aqicn.org/data-platform/token/ "
            "and add it to your .env file."
        )
    return warnings
