from sqlalchemy import JSON, Float, String, Text

try:
    from geoalchemy2 import Geometry
except ImportError:
    def Geometry(*args, **kwargs):
        return Text()

from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class Habitation(Base):
    __tablename__ = "habitations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    location: Mapped[Geometry] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    population: Mapped[int] = mapped_column(nullable=True)
    households: Mapped[int] = mapped_column(nullable=True)
    exposure_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    vulnerability_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    accessibility_info: Mapped[dict] = mapped_column(JSON, nullable=True)

