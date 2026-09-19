from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.integrations.weather import fetch_live_weather


def get_system_status():
    weather_info = fetch_live_weather()
    return {
        "model_status": settings.MODEL_STATUS,
        "model_name": "Model A (RandomForest 300 trees with GSI NLSM)",
        "forecast_horizon": settings.FORECAST_HORIZON,
        "data_status": settings.DATA_STATUS,
        "weather_status": weather_info.get("status", "ONLINE"),
        "weather_provider": weather_info.get("provider", "Open-Meteo Weather API / ECMWF IFS Model"),
        "weather_location": f"Wayanad Grid ({weather_info.get('latitude', 11.65):.2f}°N, {weather_info.get('longitude', 76.13):.2f}°E)",
        "observed_24h_mm": weather_info.get("observed_24h_mm", 0.0),
        "forecast_24h_mm": weather_info.get("forecast_24h_mm", 0.0),
        "forecast_72h_mm": weather_info.get("forecast_72h_mm", 0.0),
        "last_update": datetime.now(timezone.utc).isoformat(),
    }
