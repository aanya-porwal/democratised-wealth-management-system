"""Financial profile table — mirrors the engine's ``FinancialProfile``.

Kept in sync with ``wealth_management_system.models.base.FinancialProfile``.
All money fields are floats for engine compatibility (documented trade-off).
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey


class FinancialProfile(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """One-to-one financial snapshot for a user."""

    __tablename__ = "financial_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    monthly_income: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    employment_type: Mapped[str] = mapped_column(String(32), default="salaried_private", nullable=False)
    income_stability: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    secondary_income: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    secondary_monthly_income: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    monthly_fixed_expenses: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    monthly_variable_expenses: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    emergency_fund_months: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    existing_investments: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    provident_fund_balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    real_estate_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    gold_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    total_debt: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    monthly_emi_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    tax_bracket_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    has_term_life_insurance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_health_insurance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    existing_monthly_sip: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    extra: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="financial_profile")

