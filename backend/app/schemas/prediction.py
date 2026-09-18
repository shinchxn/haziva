from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    habitation_id: str = Field(default="hab_001")
    features: dict[str, float] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    risk: float = Field(default=0.72)
    confidence: float = Field(default=0.74)
    drivers: list[str] = Field(default_factory=list)
    timestamp: str = Field(default="2026-09-17T10:30:00")
