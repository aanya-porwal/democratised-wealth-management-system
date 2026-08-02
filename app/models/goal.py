"""Goal + GoalProgress tables."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class Goal(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A user's financial goal (mirrors engine ``Goal`` dataclass)."""

    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    goal_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_savings_for_goal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_monthly_contribution: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Integer, default=1, nullable=False)

    user: Mapped["User"] = relationship(back_populates="goals")
    progress: Mapped[list["GoalProgress"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan"
    )


class GoalProgress(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """Time-series snapshots of a goal's progress over time."""

    __tablename__ = "goal_progress"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    current_savings: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    probability_of_success: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_sip: Mapped[float | None] = mapped_column(Float, nullable=True)
    remaining_gap: Mapped[float | None] = mapped_column(Float, nullable=True)

    goal: Mapped["Goal"] = relationship(back_populates="progress")

