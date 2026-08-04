"""Behaviour drift model for digital twins.

Behavioural traits drift over time in response to life events and age.
This model provides:

* ``behaviour_from_persona`` — derive initial behaviour from a persona.
* ``apply_behaviour_drift`` — update behaviour and produce an event.
* ``risk_from_literacy`` — map literacy to a risk score.

All traits are on a 0..1 scale. The model is deliberately simple and
transparent; it only *augments* the deterministic risk engine by
modelling how behaviour changes over time.
"""

from __future__ import annotations

from typing import Dict, Optional

from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.digital_twin.models.twin import DigitalTwin
from ml.models import BehaviourTraits, Persona, RiskTolerance


def behaviour_from_persona(persona: Persona) -> BehaviourTraits:
    """Build initial behaviour traits centred on a persona's centres."""
    centres = persona.behaviour_centers
    return BehaviourTraits(
        loss_aversion=_clamp(centres.get("loss_aversion", 0.5)),
        discipline=_clamp(centres.get("discipline", 0.5)),
        financial_literacy=_clamp(centres.get("financial_literacy", 0.5)),
        overconfidence=_clamp(centres.get("overconfidence", 0.5)),
        panic_selling=_clamp(centres.get("panic_selling", 0.5)),
        long_term_thinking=_clamp(centres.get("long_term_thinking", 0.5)),
        impulse_spending=_clamp(centres.get("impulse_spending", 0.5)),
        investment_consistency=_clamp(centres.get("investment_consistency", 0.5)),
        risk_appetite=_clamp(persona.risk_center),
    )


def risk_from_literacy(literacy: float) -> RiskTolerance:
    """Map a 0..1 literacy score to a coarse risk tolerance bucket.

    This is a *behavioural* suggestion, not the deterministic risk
    engine's assessment. The engine remains authoritative.
    """
    if literacy < 0.3:
        return RiskTolerance.CONSERVATIVE
    if literacy < 0.5:
        return RiskTolerance.MODERATE
    if literacy < 0.75:
        return RiskTolerance.AGGRESSIVE
    return RiskTolerance.VERY_AGGRESSIVE


def apply_behaviour_drift(
    twin: DigitalTwin,
    drift: Dict[str, float],
    timestamp,
) -> FinancialEvent:
    """Apply a behaviour drift delta and emit a behaviour change event.

    Parameters
    ----------
    twin:
        The twin whose behaviour should change.
    drift:
        Mapping of trait name -> delta (can be negative). Applied to the
        current behaviour and clamped to [0, 1].
    timestamp:
        Time the drift occurred.

    Returns
    -------
    FinancialEvent
        The immutable ``BEHAVIOUR_CHANGE`` event (already reflected in
        the twin's current behaviour).
    """
    current = twin.behaviour
    for trait, delta in drift.items():
        if hasattr(current, trait):
            value = getattr(current, trait) + delta
            setattr(current, trait, _clamp(value))
    twin.behaviour = current
    return FinancialEvent.create(
        twin.twin_id,
        EventType.BEHAVIOUR_CHANGE,
        {"behaviour": current.to_dict(), "drift": drift},
        timestamp=timestamp,
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
