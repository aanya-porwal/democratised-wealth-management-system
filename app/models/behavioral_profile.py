"""Behavioral profile table — mirrors ``BehavioralProfile`` dataclass."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey


class BehavioralProfile(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """One-to-one behavioral traits for risk profiling."""

    __tablename__ = "behavioral_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    risk_tolerance: Mapped[str] = mapped_column(String(64), default="moderate", nullable=False)
    drawdown_reaction_score: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    has_invested_before: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_experienced_market_crash: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    financial_literacy_score: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    loss_aversion_score: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String(32), nullable=True)

    user: Mapped["User"] = relationship(back_populates="behavioral_profile")

