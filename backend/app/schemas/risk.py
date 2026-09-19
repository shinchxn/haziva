from pydantic import BaseModel, Field


class RiskProfile(BaseModel):
    current: float = Field(default=0.68)
    risk_24h: float = Field(default=0.81)
    risk_72h: float = Field(default=0.76)
    confidence: float = Field(default=0.74)
    confidence_reason: str | None = Field(default=None)
    drivers: list[str] = Field(default_factory=lambda: [
        "High landslide susceptibility",
        "High recent rainfall",
        "High forecast rainfall",
    ])
    hazard_type: str = Field(default="landslide")
    timestamp: str | None = Field(default=None)


class TrajectoryResponse(BaseModel):
    habitation_id: str
    trajectory: str
    current: float
    risk_24h: float
    risk_72h: float
    hazard_type: str = Field(default="landslide")
    timestamp: str
