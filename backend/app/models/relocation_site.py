from __future__ import annotations

from sqlalchemy import JSON, Integer, String, ForeignKey
from geoalchemy2 import Geometry
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class RelocationSite(Base):
    __tablename__ = "relocation_sites"

    site_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    habitation_id: Mapped[str] = mapped_column(ForeignKey("habitations.id"), nullable=False)
    location: Mapped[Geometry] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")
    safety_result: Mapped[str] = mapped_column(String(32), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    infrastructure_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    accessibility: Mapped[str] = mapped_column(String(64), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(String(255), nullable=True)
