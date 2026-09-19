from pydantic import BaseModel, ConfigDict, Field


class SystemStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_status: str = Field(default="ready")
    model_name: str | None = Field(default=None)
    forecast_horizon: str = Field(default="72h")
    data_status: str = Field(default="available")
    weather_status: str | None = Field(default="ONLINE")
    weather_provider: str | None = Field(default=None)
    weather_location: str | None = Field(default=None)
    observed_24h_mm: float | None = Field(default=0.0)
    forecast_24h_mm: float | None = Field(default=0.0)
    forecast_72h_mm: float | None = Field(default=0.0)
    last_update: str = Field(default="2026-09-17T10:30:00")
