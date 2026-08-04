"""Behaviour drift model for digital twins.

Behavioural traits are not static — they drift over time due to life
events (a market crash may increase loss aversion) and age (older
investors tend to be more loss-averse). This module models those
changes and emits the corresponding immutable events so the timeline
captures the evolution.
"""

from ml.digital_twin.behaviour.drift import (  # noqa: F401
    apply_behaviour_drift,
    behaviour_from_persona,
    risk_from_literacy,
)

__all__ = ["apply_behaviour_drift", "behaviour_from_persona", "risk_from_literacy"]
