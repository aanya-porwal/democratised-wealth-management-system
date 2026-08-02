"""Portfolio allocation input/output models.

``AllocationEngineInput`` captures everything the allocation engine needs
to know about a user; ``AllocationResult`` describes the recommended
target allocation across the strategic buckets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from wealth_management_system.models import UserProfile


class LiquidityNeed(str, Enum):
    """How much liquidity the user requires from the portfolio."""

    VERY_HIGH = "very_high"  # need cash within weeks (e.g. home purchase soon)
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"  # long-horizon investor, comfortable with lock-ins


@dataclass(frozen=True)
class BucketAllocation:
    """One strategic bucket's target weight.

    Attributes
    ----------
    bucket:
        Human-readable bucket name (e.g. ``"equity"``, ``"debt"``,
        ``"gold"``, ``"cash"``, ``"elss"``, ``"ppf"`` ...).
    weight:
        Target fraction of the investable corpus (0..1).
    instruments:
        Suggested concrete instruments for this bucket.
    """

    bucket: str
    weight: float
    instruments: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the weight."""
        if not (0.0 <= self.weight <= 1.0 + 1e-9):
            raise ValueError(f"bucket weight must be in [0, 1], got {self.weight}")


@dataclass
class AllocationEngineInput:
    """Everything the allocation engine needs about a user.

    Attributes
    ----------
    user:
        The root :class:`UserProfile` (carries risk, age, goals, finance).
    risk_score:
        Override for the risk score (0..100). If None the engine calls
        ``assess_risk`` itself.
    horizon_years:
        Investment horizon. If None the engine derives it from the
        longest goal / years to retirement.
    liquidity_need:
        User's liquidity preference. If None the engine derives it from
        the nearest goal and emergency-fund status.
    monthly_investment:
        Planned monthly contribution. If None the engine uses the user's
        investable surplus.
    """

    user: UserProfile
    risk_score: Optional[int] = None
    horizon_years: Optional[float] = None
    liquidity_need: Optional[LiquidityNeed] = None
    monthly_investment: Optional[float] = None


@dataclass
class AllocationResult:
    """Recommended target allocation across strategic buckets.

    Attributes
    ----------
    buckets:
        Ordered list of bucket allocations; weights sum to ~1.0.
    risk_score:
        The risk score used to derive the allocation.
    risk_category:
        Human-readable risk category.
    explanation:
        Plain-language rationale for the allocation.
    """

    buckets: list[BucketAllocation] = field(default_factory=list)
    risk_score: int = 0
    risk_category: str = ""
    explanation: str = ""

    def weight_of(self, bucket: str) -> float:
        """Target weight of one bucket (0.0 if absent)."""
        for b in self.buckets:
            if b.bucket == bucket:
                return b.weight
        return 0.0

    def total_weight(self) -> float:
        """Sum of all bucket weights (should be ~1.0)."""
        return round(sum(b.weight for b in self.buckets), 6)

    def as_dict(self) -> dict[str, float]:
        """Map bucket name -> target weight."""
        return {b.bucket: round(b.weight, 6) for b in self.buckets}
