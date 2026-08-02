"""Portfolio, PortfolioHolding and PortfolioSnapshot tables."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class Portfolio(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A named portfolio owned by a user."""

    __tablename__ = "portfolios"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_allocation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Integer, default=1, nullable=False)

    user: Mapped["User"] = relationship(back_populates="portfolios")
    holdings: Mapped[list["PortfolioHolding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["PortfolioSnapshot"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class PortfolioHolding(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """A single position inside a portfolio."""

    __tablename__ = "portfolio_holdings"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_class: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    bucket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    market_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_basis: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")


class PortfolioSnapshot(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """Time-series snapshot of a portfolio's value and weights."""

    __tablename__ = "portfolio_snapshots"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True, nullable=False)
    total_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cash_flow: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="snapshots")

