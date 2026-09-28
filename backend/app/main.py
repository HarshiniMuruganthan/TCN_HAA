"""
main.py — FastAPI application entry point.

Startup sequence
----------------
1. Validate environment config (warn if token missing)
2. Initialise SQLite database
3. Register all routers
4. Start background APScheduler (auto-collects live AQI every hour)
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes.aqi_routes import router as aqi_router
from backend.app.routes.live_routes import router as live_router
from backend.app.services.live_aqi_service import get_all_cities_live
from backend.app.utils.config import (
    COLLECTION_INTERVAL_MINUTES,
    validate_config,
)
from backend.app.utils.database import init_db, save_observation

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title="AQI Health Risk Prediction API",
    description=(
        "Real-time AQI monitoring, TCN-HAA forecasting, "
        "health risk analysis, anomaly detection and early warning."
    ),
    version="2.0.0",
)


# ── CORS (Allows all localhost dev ports e.g. 5173, 5174, 3000) ──────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(aqi_router)   # /api/cities, /api/aqi, /api/prediction, /api/dashboard
app.include_router(live_router)  # /api/live, /api/history, /api/ranking, /api/status


# ── Background job: auto-collect live AQI every N minutes ────
def _collect_all_cities() -> None:
    """
    Called by APScheduler every COLLECTION_INTERVAL_MINUTES.
    Fetches live AQI for all supported cities and stores results.
    """
    logger.info("Scheduler: Starting auto-collection for all cities…")
    results = get_all_cities_live()
    saved = 0
    for city, data in results.items():
        if data:
            obs = save_observation(data)
            if obs:
                saved += 1
    logger.info(
        "Scheduler: Auto-collection complete — %d/%d cities saved.",
        saved, len(results),
    )


# ── Startup event ──────────────────────────────────────────────
@app.on_event("startup")
def startup_event() -> None:

    # 1. Config validation
    warnings = validate_config()
    for w in warnings:
        logger.warning("CONFIG: %s", w)

    # 2. Database init
    init_db()

    # 3. Collect live data immediately on startup
    logger.info("Startup: Running initial data collection…")
    _collect_all_cities()

    # 4. Start background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _collect_all_cities,
        trigger="interval",
        minutes=COLLECTION_INTERVAL_MINUTES,
        id="auto_collect_aqi",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started — collecting every %d minutes.",
        COLLECTION_INTERVAL_MINUTES,
    )


# ── Root endpoints ────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "AeroRisk AI Backend API v2.0 is active and running",
        "docs":    "/docs",
        "live_api": "/api/live/Chennai",
        "dashboard_api": "/api/live-dashboard/Chennai",
        "status":  "/api/status",
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}