from datetime import datetime, timezone

from backend.app.core.config import settings


def get_system_status():
    return {
        "model_status": settings.MODEL_STATUS,
        "forecast_horizon": settings.FORECAST_HORIZON,
        "data_status": settings.DATA_STATUS,
        "last_update": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
