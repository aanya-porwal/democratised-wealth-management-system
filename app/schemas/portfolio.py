"""Portfolio schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HoldingCreate(BaseModel):
    """Add/update a holding in a portfolio."""

    asset_class: str = Field(..., description="Engine AssetClass value, e.g. equity_index_largecap")
    bucket: str | None = Field(None, max_length=32)
    market_value: float = Field(..., ge=0)
    cost_basis: float = Field(0, ge=0)
    quantity: float | None = None
    currency: str = "INR"


class HoldingOut(BaseModel):
    """Holding response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    portfolio_id: uuid.UUID
    asset_class: str
    bucket: str | None = None
    market_value: float
    cost_basis: float
    quantity: float | None = None
    currency: str
    created_at: datetime


class PortfolioCreate(BaseModel):
    """Create a portfolio."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_allocation: dict[str, float] | None = None


class PortfolioOut(BaseModel):
    """Portfolio response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None = None
    total_value: float
    target_allocation: dict | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class PortfolioSnapshotOut(BaseModel):
    """Snapshot response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    portfolio_id: uuid.UUID
    captured_at: datetime
    total_value: float
    weights: dict | None = None
    cash_flow: float | None = None
    notes: str | None = None

