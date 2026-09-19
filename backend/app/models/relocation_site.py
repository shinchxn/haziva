from sqlalchemy import JSON, Float, Integer, String, Text, ForeignKey

try:
    from geoalchemy2 import Geometry
except ImportError:
    def Geometry(*args, **kwargs):
        return Text()

from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class RelocationSite(Base):
    __tablename__ = "relocation_sites"

    site_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    habitation_id: Mapped[str | None] = mapped_column(ForeignKey("habitations.id"), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facility_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    location: Mapped[Geometry] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")
    safety_result: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity_status: Mapped[str | None] = mapped_column(String(32), nullable=True, default="HEURISTIC")
    infrastructure_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    accessibility: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    transparent_priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ranking_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

