"""SimulationResult and ScenarioAnalysis tables."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class SimulationResult(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A persisted Monte Carlo simulation result."""

    __tablename__ = "simulation_results"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("goals.id", ondelete="SET NULL"), index=True, nullable=True
    )
    run_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    simulation_type: Mapped[str] = mapped_column(String(32), default="monte_carlo", index=True, nullable=False)
    simulations: Mapped[int] = mapped_column(Float, default=10000, nullable=False)
    horizon_years: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return: Mapped[float] = mapped_column(Float, nullable=False)
    volatility: Mapped[float] = mapped_column(Float, nullable=False)
    inflation: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_investment: Mapped[float] = mapped_column(Float, nullable=False)
    initial_corpus: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    median: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentile_5: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentile_25: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentile_75: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentile_95: Mapped[float | None] = mapped_column(Float, nullable=True)
    worst_case: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_case: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    std_dev: Mapped[float | None] = mapped_column(Float, nullable=True)
    probability_of_success: Mapped[float | None] = mapped_column(Float, nullable=True)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    statistics: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ScenarioAnalysis(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A persisted what-if scenario analysis."""

    __tablename__ = "scenario_analyses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    run_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    adjustments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    goal_probabilities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_required_sip: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_worth: Mapped[float | None] = mapped_column(Float, nullable=True)
    allocation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(String(1024), nullable=True)

