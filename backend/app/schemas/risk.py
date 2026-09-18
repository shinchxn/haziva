from pydantic import BaseModel, Field


class RiskProfile(BaseModel):
    current: float = Field(default=0.68)
    risk_24h: float = Field(default=0.81)
    risk_72h: float = Field(default=0.76)
    confidence: float = Field(default=0.74)
    drivers: list[str] = Field(default_factory=lambda: [
        "High landslide susceptibility",
        "High recent rainfall",
        "High forecast rainfall",
    ])
    timestamp: str | None = Field(default=None)
