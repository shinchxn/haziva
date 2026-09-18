from __future__ import annotations

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class Habitation(Base):
    __tablename__ = "habitations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Geometry] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    population: Mapped[int] = mapped_column(nullable=True)
    households: Mapped[int] = mapped_column(nullable=True)
    exposure_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    vulnerability_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    accessibility_info: Mapped[dict] = mapped_column(JSON, nullable=True)
