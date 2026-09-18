from datetime import datetime, timezone


class Settings:
    PROJECT_NAME: str = "Haziva Backend"
    API_PREFIX: str = "/"
    DESCRIPTION: str = "Disaster risk assessment and relocation backend"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/haziva"
    MODEL_STATUS: str = "ready"
    FORECAST_HORIZON: str = "72h"
    DATA_STATUS: str = "available"
    LAST_UPDATE: datetime = datetime.now(timezone.utc)


settings = Settings()
