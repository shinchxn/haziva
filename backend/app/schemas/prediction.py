from typing import Any

from pydantic import BaseModel, Field, field_validator


class PredictionFeatures(BaseModel):
    slope: float = Field(default=0.5, ge=0.0, le=1.0)
    rainfall: float = Field(default=0.5, ge=0.0, le=1.0)
    forecast_rainfall: float = Field(default=0.5, ge=0.0, le=1.0)
    susceptibility: float = Field(default=0.5, ge=0.0, le=1.0)
    population_exposure: float = Field(default=0.5, ge=0.0, le=1.0)
    accessibility: float = Field(default=0.5, ge=0.0, le=1.0)


class PredictionRequest(BaseModel):
    habitation_id: str = Field(default="hab_001")
    hazard_type: str = Field(default="landslide")
    features: dict[str, float] | PredictionFeatures = Field(default_factory=dict)

    @field_validator("features", mode="after")
    @classmethod
    def validate_features(cls, v: Any) -> dict[str, float]:
        if isinstance(v, PredictionFeatures):
            return v.model_dump()
        if isinstance(v, dict):
            for key, val in v.items():
                if isinstance(val, (int, float)):
                    if val < 0.0 or val > 1.0:
                        raise ValueError(f"Feature '{key}' value {val} must be between 0.0 and 1.0")
            return v
        return {}


class PredictionResponse(BaseModel):
    risk: float = Field(default=0.72)
    confidence: float = Field(default=0.74)
    drivers: list[str] = Field(default_factory=list)
    hazard_type: str = Field(default="landslide")
    timestamp: str = Field(default="2026-09-18T10:00:00Z")
