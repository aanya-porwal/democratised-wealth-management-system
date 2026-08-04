"""Behavioural decision model — PART 4.

A probabilistic, behaviour-driven model of how a synthetic user responds
to a recommendation. Behavioural traits modulate the base acceptance
probability:

* **Loss aversion** lowers acceptance of risk-increasing actions.
* **Financial literacy** raises acceptance of well-reasoned actions.
* **Panic selling** raises the chance of rejecting/ignoring during
  market drawdowns.
* **Discipline** and **investment consistency** raise acceptance of
  long-horizon rebalancing actions.
* **Overconfidence** raises acceptance of aggressive/security actions.

The model is deliberately not a deterministic engine: it only produces
probabilities, which downstream consumers sample. No deterministic
financial math is replaced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Dict, List, Optional

from ml.models import BehaviourTraits, FinancialTwinProfile
from ml.utils.logging import get_logger

logger = get_logger(__name__)


class DecisionOutcome(str, Enum):
    """The possible outcomes of a behavioural decision."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IGNORED = "ignored"
    MODIFIED = "modified"


@dataclass
class BehaviouralDecisionModel:
    """Statistically modulate the probability of a recommendation outcome.

    Parameters
    ----------
    behaviour:
        The :class:`~ml.models.BehaviourTraits` of the synthetic user.
    profile:
        Optional :class:`~ml.models.FinancialTwinProfile` for context.
    """

    behaviour: BehaviourTraits
    profile: Optional[FinancialTwinProfile] = None

    # ── trait weights (higher = more influence, sign = direction) ──
    _TRAIT_WEIGHTS: ClassVar[Dict[str, float]] = {
        "loss_aversion": -0.30,
        "financial_literacy": 0.25,
        "panic_selling": -0.20,
        "discipline": 0.20,
        "investment_consistency": 0.15,
        "overconfidence": 0.15,
        "long_term_thinking": 0.10,
        "impulse_spending": -0.10,
    }

    def acceptance_probability(self, category: str = "asset_allocation") -> float:
        """Compute the probability the user accepts a recommendation.

        The base probability is drawn from the config's acceptance table
        (per category) then modulated by behavioural traits. The result
        is a probability in ``[0, 1]``.

        Parameters
        ----------
        category:
            Recommendation category (e.g. ``asset_allocation``). Used to
            look up the base acceptance rate.

        Returns
        -------
        float
            Acceptance probability.
        """
        from ml.config import get_config

        cfg = get_config()
        base = cfg.recommendation.acceptance.get(category, 0.45)

        # Trait modulation centred around the default trait value (0.5).
        modulation = 0.0
        for trait, weight in self._TRAIT_WEIGHTS.items():
            value = getattr(self.behaviour, trait, 0.5)
            modulation += weight * (value - 0.5)

        prob = base + modulation
        # Clamp to a sane range (avoid 0/1 extremes).
        return max(0.05, min(0.98, prob))

    def probability_by_outcome(self, category: str = "asset_allocation") -> Dict[str, float]:
        """Return the probability of each outcome for a category.

        The remaining probability after acceptance is distributed among
        the other outcomes (rejected / ignored / modified), weighted by
        behaviour. ``panic_selling`` and ``impulse_spending`` shift
        weight toward ``ignored``/``rejected``; ``discipline`` and
        ``financial_literacy`` shift toward ``modified``.

        Returns
        -------
        Dict[str, float]
            A mapping ``outcome -> probability`` summing to 1.
        """
        accepted = self.acceptance_probability(category)
        remaining = 1.0 - accepted

        # Behaviour-dependent split of the non-accepted mass. Weights are
        # clamped to be non-negative so the resulting distribution is
        # always valid (a probability vector).
        panic = max(0.1, min(1.0, getattr(self.behaviour, "panic_selling", 0.5)))
        discipline = max(0.1, min(1.0, getattr(self.behaviour, "discipline", 0.5)))
        literacy = max(0.1, min(1.0, getattr(self.behaviour, "financial_literacy", 0.5)))
        modified_weight = max(0.05, 0.3 + 0.3 * discipline + 0.2 * literacy)
        ignored_weight = max(0.05, 0.3 + 0.3 * panic)
        rejected_weight = max(0.05, 1.0 - modified_weight - ignored_weight)

        total = modified_weight + ignored_weight + rejected_weight
        return {
            DecisionOutcome.ACCEPTED.value: accepted,
            DecisionOutcome.MODIFIED.value: remaining * modified_weight / total,
            DecisionOutcome.IGNORED.value: remaining * ignored_weight / total,
            DecisionOutcome.REJECTED.value: remaining * rejected_weight / total,
        }

    def decide(self, category: str = "asset_allocation") -> DecisionOutcome:
        """Sample a single outcome given the behaviour-driven probabilities.

        Parameters
        ----------
        category:
            Recommendation category.

        Returns
        -------
        DecisionOutcome
            The sampled outcome.
        """
        import numpy as np

        from ml.utils.seeding import get_rng

        rng = get_rng()
        probs = self.probability_by_outcome(category)
        outcomes = list(probs.keys())
        weights = [probs[o] for o in outcomes]
        return DecisionOutcome(rng.choice(outcomes, p=weights))


def decide_recommendation_acceptance(
    behaviour: BehaviourTraits,
    category: str = "asset_allocation",
    profile: Optional[FinancialTwinProfile] = None,
) -> DecisionOutcome:
    """Convenience wrapper to sample a decision outcome.

    Parameters
    ----------
    behaviour:
        The behavioural traits of the user.
    category:
        Recommendation category.
    profile:
        Optional profile for context.

    Returns
    -------
    DecisionOutcome
        The sampled outcome.
    """
    model = BehaviouralDecisionModel(behaviour=behaviour, profile=profile)
    return model.decide(category)


def rerank_by_behavior(
    items: List[Dict],
    behaviour: BehaviourTraits,
    score_key: str = "score",
) -> List[Dict]:
    """Rerank a list of ranked items by behavioural affinity.

    This *augments* the deterministic ranking (score) with a behavioural
    preference term. It does not replace the deterministic score — it
    only reorders items that are otherwise close.

    Parameters
    ----------
    items:
        A list of dicts, each with a ``score_key`` numeric field.
    behaviour:
        The behavioural traits used to adjust the effective score.
    score_key:
        The key holding the deterministic score.

    Returns
    -------
    List[Dict]
        The items reranked by ``score + behaviour_affinity``.
    """
    # Preference for long-term, low-impulse products vs short-term.
    long_term_pref = behaviour.long_term_thinking - 0.5
    impulse_penalty = behaviour.impulse_spending - 0.5

    def _effective(item: Dict) -> float:
        base = float(item.get(score_key, 0.0))
        # Long-term products get a small boost for long-term thinkers.
        product_type = str(item.get("type", ""))
        if "long_term" in product_type or "index" in product_type or "life" in product_type:
            base += long_term_pref * 2.0
        if "guaranteed" in product_type or "fixed" in product_type:
            base -= impulse_penalty * 2.0
        return base

    ranked = sorted(items, key=_effective, reverse=True)
    return ranked
