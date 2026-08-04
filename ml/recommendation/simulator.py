"""Recommendation & interaction simulation (PART 6).

A :class:`RecommendationRecord` describes a single recommendation issued
to a synthetic user. The :class:`RecommendationSimulator` generates
recommendations and simulates the user's response using the behaviour-
driven decision model from :mod:`ml.behaviour` — so the acceptance
reflects the user's loss aversion, financial literacy, impulse spending,
etc.

The interaction history is logged as records; these become the labels
for the recommendation-acceptance ML model.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ml.behaviour.decision import (
    BehaviouralDecisionModel,
    DecisionOutcome,
)
from ml.config import get_config
from ml.models import BehaviourTraits, FinancialTwinProfile
from ml.utils.logging import get_logger
from ml.utils.seeding import get_rng

logger = get_logger(__name__)


@dataclass
class RecommendationRecord:
    """A single recommendation and its simulated interaction outcome.

    Attributes
    ----------
    recommendation_id:
        Unique id for the recommendation.
    twin_id:
        The synthetic user.
    category:
        Recommendation category (e.g. asset_allocation, emergency_fund).
    title:
        Human-readable title.
    priority:
        Priority score (0..1).
    outcome:
        The simulated interaction outcome.
    confidence:
        The model's confidence in the recommendation.
    risk_level:
        The risk level implied by the recommendation.
    created_at:
        When the recommendation was issued.
    """

    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    twin_id: str = ""
    category: str = "asset_allocation"
    title: str = ""
    priority: float = 0.5
    outcome: str = "ignored"
    confidence: float = 0.6
    risk_level: str = "moderate"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, object]:
        return {
            "recommendation_id": self.recommendation_id,
            "twin_id": self.twin_id,
            "category": self.category,
            "title": self.title,
            "priority": self.priority,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat(),
        }


class RecommendationSimulator:
    """Generate and simulate recommendations for synthetic users.

    Parameters
    ----------
    behaviour:
        Behavioural traits used to simulate the response.
    profile:
        Optional financial profile for context.
    """

    def __init__(
        self,
        behaviour: BehaviourTraits,
        profile: Optional[FinancialTwinProfile] = None,
    ) -> None:
        self._behaviour = behaviour
        self._profile = profile
        self._decision = BehaviouralDecisionModel(behaviour=behaviour, profile=profile)
        self._cfg = get_config()

    # ── generate ───────────────────────────────────────────────────
    def generate_recommendation(
        self,
        twin_id: str,
        category: Optional[str] = None,
        include_title: bool = True,
    ) -> RecommendationRecord:
        """Generate a single recommendation for a user.

        The category is chosen deterministically from the config
        categories (if provided) or randomly.

        Parameters
        ----------
        twin_id:
            The synthetic user id.
        category:
            Optional category override.
        include_title:
            Whether to fill a default title.

        Returns
        -------
        RecommendationRecord
            The generated recommendation (with a simulated outcome).
        """
        rng = get_rng()
        categories = list(self._cfg.recommendation.categories)
        if category is None:
            category = rng.choice(categories) if categories else "asset_allocation"
        title = self._title_for(category) if include_title else ""
        outcome = self._decision.decide(category)
        risk_level = self._risk_level_for(category)
        return RecommendationRecord(
            twin_id=twin_id,
            category=category,
            title=title,
            priority=float(rng.uniform(0.3, 0.95)),
            outcome=outcome.value,
            confidence=float(rng.uniform(0.5, 0.95)),
            risk_level=risk_level,
        )

    def generate_batch(
        self,
        twin_id: str,
        n: int = 5,
    ) -> List[RecommendationRecord]:
        """Generate ``n`` recommendations for a user.

        Returns
        -------
        List[RecommendationRecord]
            The generated recommendations with simulated outcomes.
        """
        return [self.generate_recommendation(twin_id) for _ in range(n)]

    # ── helpers ───────────────────────────────────────────────────
    def _title_for(self, category: str) -> str:
        titles = {
            "asset_allocation": "Increase equity allocation for long-term goals",
            "emergency_fund": "Build an emergency fund of 6 months of expenses",
            "insurance": "Consider term life insurance for dependents",
            "retirement": "Increase retirement contributions",
            "debt": "Prioritise high-interest debt repayment",
            "tax": "Optimise tax-saving investments",
            "rebalance": "Rebalance portfolio to target allocation",
        }
        return titles.get(category, f"{category.replace('_', ' ').title()} recommendation")

    def _risk_level_for(self, category: str) -> str:
        high_risk = {"asset_allocation", "equity", "aggressive"}
        if category in high_risk:
            return "high"
        if category in {"emergency_fund", "insurance", "debt", "tax"}:
            return "low"
        return "moderate"


def simulate_recommendation_interaction(
    behaviour: BehaviourTraits,
    twin_id: str,
    category: Optional[str] = None,
    profile: Optional[FinancialTwinProfile] = None,
) -> RecommendationRecord:
    """Convenience wrapper for a single recommendation interaction."""
    sim = RecommendationSimulator(behaviour=behaviour, profile=profile)
    return sim.generate_recommendation(twin_id, category=category)
