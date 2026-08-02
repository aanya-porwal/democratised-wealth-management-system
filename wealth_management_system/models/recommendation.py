"""Explainable recommendation models.

Every recommendation carries a confidence level and a list of
human-readable reasons so the user understands *why* a product was
chosen and *how sure* the engine is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConfidenceLevel(str, Enum):
    """How confident the engine is in a recommendation."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationType(str, Enum):
    """What kind of recommendation this is."""

    ASSET_ALLOCATION = "asset_allocation"
    INSTRUMENT = "instrument"
    REBALANCE = "rebalance"
    GOAL = "goal"
    PROTECTION = "protection"
    TAX = "tax"
    GENERAL = "general"


@dataclass(frozen=True)
class RecommendationReason:
    """A single explanation for a recommendation.

    Attributes
    ----------
    text:
        Human-readable reason (e.g. ``"saves tax via Section 80C"``).
    weight:
        Optional numeric weight (0..1) indicating how much this reason
        contributed to the recommendation.
    """

    text: str
    weight: float = 1.0


@dataclass
class Recommendation:
    """A single explainable recommendation.

    Attributes
    ----------
    recommendation_type:
        The kind of recommendation.
    title:
        Short title (e.g. ``"Invest in ELSS"``).
    description:
        Longer plain-language description.
    confidence:
        Confidence level.
    reasons:
        Ordered list of reasons (most important first).
    action:
        Optional machine-readable action key.
    impact:
        Optional estimated impact (e.g. rupees saved or probability lift).
    """

    recommendation_type: RecommendationType
    title: str
    description: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    reasons: list[RecommendationReason] = field(default_factory=list)
    action: Optional[str] = None
    impact: Optional[str] = None

    def add_reason(self, text: str, weight: float = 1.0) -> None:
        """Append a reason and keep the list sorted by weight (desc)."""
        self.reasons.append(RecommendationReason(text=text, weight=weight))
        self.reasons.sort(key=lambda r: r.weight, reverse=True)

    def reason_texts(self) -> list[str]:
        """Just the human-readable reasons, in order."""
        return [r.text for r in self.reasons]
