"""Rebalancing engine models.

These describe the outcome of a portfolio-rebalancing check: whether a
rebalance is warranted, what trades to execute, and the tax/cost impact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from wealth_management_system.models.portfolio import Trade


class RebalanceDirection(str, Enum):
    """Whether a position must be trimmed or topped up."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class RebalanceAction:
    """A single required adjustment for one bucket.

    Attributes
    ----------
    bucket:
        Strategic bucket name (e.g. ``"equity"``).
    direction:
        ``buy`` / ``sell`` / ``hold``.
    current_weight:
        Current weight of the bucket (0..1).
    target_weight:
        Target weight of the bucket (0..1).
    drift:
        Absolute drift (current - target) in weight terms.
    trade_amount:
        Rupee notional to trade (0 for hold).
    reason:
        Plain-language explanation.
    """

    bucket: str
    direction: RebalanceDirection
    current_weight: float
    target_weight: float
    drift: float
    trade_amount: float
    reason: str = ""


@dataclass
class RebalanceResult:
    """The complete rebalancing analysis.

    Attributes
    ----------
    rebalance_required:
        Whether any bucket drifted beyond the threshold.
    actions:
        Per-bucket actions (only buckets that need adjusting).
    trades:
        Concrete instrument-level trades implied by the actions.
    total_transaction_cost:
        Sum of transaction costs across all trades.
    total_tax_impact:
        Estimated capital-gains tax on the sales.
    portfolio_value:
        Total portfolio value used for the analysis.
    notes:
        Additional context (e.g. "no rebalance needed").
    """

    rebalance_required: bool
    actions: list[RebalanceAction] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    total_transaction_cost: float = 0.0
    total_tax_impact: float = 0.0
    portfolio_value: float = 0.0
    notes: list[str] = field(default_factory=list)

    def total_trade_notional(self) -> float:
        """Sum of absolute trade amounts (both buys and sells)."""
        return round(sum(t.absolute_amount for t in self.trades), 2)
