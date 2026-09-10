from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes.aqi_routes import router as aqi_router


app = FastAPI(
    title="AQI Health Risk Prediction API",
    description="API for AQI monitoring, TCN prediction and health risk analysis",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(aqi_router)


@app.get("/")
def root():
    return {
        "message": "AQI Health Risk Prediction API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }