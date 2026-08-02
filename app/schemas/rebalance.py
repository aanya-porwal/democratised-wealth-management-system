"""Rebalancing schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RebalanceActionOut(BaseModel):
    """One bucket-level rebalancing action."""

    bucket: str
    direction: str
    current_weight: float
    target_weight: float
    drift: float
    trade_amount: float
    reason: str = ""


class RebalanceTradeOut(BaseModel):
    """One instrument-level trade."""

    asset_class: str
    amount: float
    reason: str = ""
    estimated_tax_impact: float = 0.0
    estimated_transaction_cost: float = 0.0


class RebalanceOut(BaseModel):
    """Rebalancing analysis response."""

    rebalance_required: bool
    actions: list[RebalanceActionOut] = []
    trades: list[RebalanceTradeOut] = []
    total_transaction_cost: float = 0.0
    total_tax_impact: float = 0.0
    portfolio_value: float = 0.0
    notes: list[str] = []

