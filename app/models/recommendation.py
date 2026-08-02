"""Recommendation table — stores explainable engine recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class Recommendation(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A persisted recommendation produced by the recommendation engine."""

    __tablename__ = "recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recommendation_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    impact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[int | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)

