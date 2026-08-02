"""FinancialHealthScore table — stores health score snapshots."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class FinancialHealthScore(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A persisted 0-100 financial health assessment."""

    __tablename__ = "financial_health_scores"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    scored_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    score: Mapped[int] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    factors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list | None] = mapped_column(JSON, nullable=True)

