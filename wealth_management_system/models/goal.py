"""Goal analysis models for the production goal engine.

``GoalAnalysis`` is the rich per-goal result carrying every field the
business requires (name, type, priority, current amount, target amount,
progress, target date, years remaining, inflation, expected return,
required SIP, probability of success, and the derived projections).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class GoalVerdict(str, Enum):
    """Plain-language outlook for a goal."""

    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    UNLIKELY = "unlikely"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class GoalAnalysis:
    """The complete analytical picture for one goal.

    Attributes
    ----------
    name:
        Human-readable goal name (falls back to the goal type).
    goal_type:
        Value of the ``GoalType`` enum (e.g. ``"retirement"``).
    priority:
        Value of the ``GoalPriority`` enum.
    current_amount:
        Already saved towards the goal.
    target_amount:
        Nominal target (pre-inflation adjustment).
    current_progress:
        Fraction of the (inflation-adjusted) target already saved (0..1).
    target_date:
        When the money is needed.
    years_remaining:
        Years from today to the target date.
    inflation_rate:
        Assumed annual inflation for this goal.
    expected_return:
        Assumed annual return for the goal's corpus.
    inflation_adjusted_target:
        Target amount inflated to the target date in today's terms.
    future_value:
        Projected corpus at the target date on the current path.
    present_value:
        Present value (today's money) of the inflation-adjusted target.
    required_sip:
        Monthly contribution needed to hit the target from today.
    remaining_gap:
        Rupees still short of the target at the target date on the
        current path.
    expected_corpus:
        Expected (median) corpus from simulation, if available.
    probability_of_success:
        Monte-Carlo probability (0..1) of reaching the target.
    verdict:
        Plain-language outlook derived from the probability.
    notes:
        Additional explainability notes.
    """

    name: str
    goal_type: str
    priority: str
    current_amount: float
    target_amount: float
    current_progress: float
    target_date: date
    years_remaining: float
    inflation_rate: float
    expected_return: float
    inflation_adjusted_target: float
    future_value: float
    present_value: float
    required_sip: float
    remaining_gap: float
    expected_corpus: Optional[float] = None
    probability_of_success: Optional[float] = None
    verdict: GoalVerdict = GoalVerdict.NOT_APPLICABLE
    notes: list[str] = field(default_factory=list)


@dataclass
class GoalAnalysisResult:
    """Aggregate goal analysis for a user (multiple goals)."""

    goals: list[GoalAnalysis] = field(default_factory=list)

    def total_required_sip(self) -> float:
        """Sum of required SIPs across all goals."""
        return round(sum(g.required_sip for g in self.goals), 2)

    def total_remaining_gap(self) -> float:
        """Sum of remaining gaps across all goals."""
        return round(sum(g.remaining_gap for g in self.goals), 2)

    def goal_by_name(self, name: str) -> Optional[GoalAnalysis]:
        """Find one goal analysis by name (case-insensitive)."""
        lowered = name.lower()
        for g in self.goals:
            if g.name.lower() == lowered:
                return g
        return None
