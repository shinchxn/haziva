from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Haziva Backend"
    API_PREFIX: str = "/"
    DESCRIPTION: str = "Disaster risk assessment and relocation backend"
    ENVIRONMENT: str = "development"
    TESTING: bool = False
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/haziva"
    CORS_ORIGINS: list[str] = ["*"]
    MODEL_STATUS: str = "ready"
    FORECAST_HORIZON: str = "72h"
    DATA_STATUS: str = "available"
    LAST_UPDATE: str = "2026-09-18T10:00:00Z"


settings = Settings()
