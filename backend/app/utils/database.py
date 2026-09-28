"""
database.py — SQLite database for storing live AQI observations.

Every time the live API is called, a row is saved here.
This builds a live historical dataset over time.

Table schema
------------
aqi_history
  id          INTEGER PRIMARY KEY AUTOINCREMENT
  city        TEXT    NOT NULL
  timestamp   TEXT    NOT NULL (ISO-8601)
  aqi         REAL    NOT NULL
  pm25        REAL
  pm10        REAL
  no2         REAL
  so2         REAL
  co          REAL
  o3          REAL
  source      TEXT    (e.g. "aqicn" or "mock")
"""

import logging
import os
from datetime import datetime

from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.utils.config import BASE_DIR

logger = logging.getLogger(__name__)

# ── Database file path ────────────────────────────────────────
_DB_PATH = os.path.join(BASE_DIR, "data", "aqi_live.db")
_DB_URL = f"sqlite:///{_DB_PATH}"


# ── SQLAlchemy setup ──────────────────────────────────────────
engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── ORM model ─────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class AQIObservation(Base):
    """One row = one live API observation for one city."""

    __tablename__ = "aqi_history"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    city      = Column(String(100), nullable=False, index=True)
    timestamp = Column(Text, nullable=False)
    aqi       = Column(Float, nullable=False)
    pm25      = Column(Float, nullable=True)
    pm10      = Column(Float, nullable=True)
    no2       = Column(Float, nullable=True)
    so2       = Column(Float, nullable=True)
    co        = Column(Float, nullable=True)
    o3        = Column(Float, nullable=True)
    source    = Column(String(50), nullable=True, default="aqicn")


# ── Create tables if they don't exist ────────────────────────
def init_db() -> None:
    """Create all tables. Called on app startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised at: %s", _DB_PATH)


# ── Save a live observation ───────────────────────────────────
def save_observation(data: dict) -> AQIObservation | None:
    """
    Save one validated live AQI reading to the database.

    Parameters
    ----------
    data : dict
        A sanitised dict from live_aqi_service.get_live_aqi()

    Returns
    -------
    AQIObservation | None
    """
    try:
        obs = AQIObservation(
            city      = data.get("city", ""),
            timestamp = data.get("timestamp", datetime.now().isoformat()),
            aqi       = float(data["aqi"]),
            pm25      = data.get("pm25"),
            pm10      = data.get("pm10"),
            no2       = data.get("no2"),
            so2       = data.get("so2"),
            co        = data.get("co"),
            o3        = data.get("o3"),
            source    = data.get("source", "aqicn"),
        )

        with SessionLocal() as session:
            session.add(obs)
            session.commit()
            session.refresh(obs)
            logger.info(
                "Saved observation — city: %s, AQI: %s, id: %s",
                obs.city, obs.aqi, obs.id,
            )
            return obs

    except Exception as exc:
        logger.error("Failed to save observation: %s", exc)
        return None


# ── Query helpers ─────────────────────────────────────────────
def get_recent_history(city: str, limit: int = 24) -> list[dict]:
    """
    Return the most recent `limit` observations for a city.
    Default: last 24 readings (≈ 24 hours if collected hourly).
    """
    with SessionLocal() as session:
        rows = (
            session.query(AQIObservation)
            .filter(AQIObservation.city.ilike(f"%{city}%"))
            .order_by(AQIObservation.id.desc())
            .limit(limit)
            .all()
        )

    # Return newest-first list of dicts
    return [
        {
            "id":        r.id,
            "city":      r.city,
            "timestamp": r.timestamp,
            "aqi":       r.aqi,
            "pm25":      r.pm25,
            "pm10":      r.pm10,
            "no2":       r.no2,
            "so2":       r.so2,
            "co":        r.co,
            "o3":        r.o3,
            "source":    r.source,
        }
        for r in rows
    ]


def get_all_latest() -> list[dict]:
    """
    Return the most recent observation for every city.
    Used for city ranking.
    """
    with SessionLocal() as session:
        # Subquery: max id per city
        subq = (
            session.query(
                AQIObservation.city,
                AQIObservation.id.label("max_id"),
            )
            .group_by(AQIObservation.city)
            .subquery()
        )

        rows = (
            session.query(AQIObservation)
            .join(subq, AQIObservation.id == subq.c.max_id)
            .all()
        )

    return [
        {
            "city":      r.city,
            "aqi":       r.aqi,
            "timestamp": r.timestamp,
        }
        for r in rows
    ]


def count_observations(city: str | None = None) -> int:
    """Return total number of stored observations (optionally filtered by city)."""
    with SessionLocal() as session:
        q = session.query(AQIObservation)
        if city:
            q = q.filter(AQIObservation.city.ilike(f"%{city}%"))
        return q.count()
