from pydantic import BaseModel, ConfigDict, Field


class SystemStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_status: str = Field(default="ready")
    forecast_horizon: str = Field(default="72h")
    data_status: str = Field(default="available")
    last_update: str = Field(default="2026-09-17T10:30:00")
