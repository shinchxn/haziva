from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HabitationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default="hab_001")
    name: str = Field(default="Habitation A")
    latitude: float = Field(default=11.6)
    longitude: float = Field(default=76.0)
    priority: str = Field(default="High")
    current_risk: float = Field(default=0.72)


class HabitationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    location: dict[str, Any]
    latitude: float
    longitude: float
    population: int
    households: int
    exposure_info: dict[str, Any]
    vulnerability_info: dict[str, Any]
    accessibility_info: dict[str, Any]
    current_risk: float
    risk_24h: float
    risk_72h: float
    priority: str
