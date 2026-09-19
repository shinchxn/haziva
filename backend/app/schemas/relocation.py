from typing import Any

from pydantic import BaseModel, Field


class RelocationSite(BaseModel):
    site_id: str
    name: str | None = None
    facility_category: str | None = None
    status: str = Field(default="candidate")
    safety: str = Field(default="INSUFFICIENT_EVIDENCE")
    capacity: int | None = None
    capacity_status: str | None = Field(default="HEURISTIC")
    accessibility: str | None = None
    infrastructure: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    rejection_reason: str | None = None
    transparent_priority_score: float | None = None
    ranking_explanation: str | None = None


class RelocationProfile(BaseModel):
    habitation_id: str
    sites: list[RelocationSite] = Field(default_factory=list)
    status: str = Field(default="OK")
    message: str | None = None
