from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class Risk(Base):
    __tablename__ = "risks"

    habitation_id: Mapped[str] = mapped_column(ForeignKey("habitations.id"), primary_key=True)
    current_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_24h: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_72h: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trajectory: Mapped[str] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    risk_drivers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
