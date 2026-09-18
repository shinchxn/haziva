from typing import Any

from pydantic import BaseModel, Field


class RelocationSite(BaseModel):
    site_id: str = Field(default="site_001")
    status: str = Field(default="candidate")
    safety: str = Field(default="pass")
    capacity: int = Field(default=850)
    accessibility: str | None = None
    infrastructure: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    rejection_reason: str | None = None


class RelocationProfile(BaseModel):
    habitation_id: str = Field(default="hab_001")
    sites: list[RelocationSite] = Field(default_factory=lambda: [
        {
            "site_id": "site_001",
            "status": "candidate",
            "safety": "pass",
            "capacity": 850,
        }
    ])
