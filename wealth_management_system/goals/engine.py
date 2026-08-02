"""Goal planning engine.

Produces a complete, explainable analytical picture for every goal in a
user's plan. It answers the questions a financial planner would ask:

* How much will the goal cost in the future once inflation is applied?
* What is that future cost in today's money?
* How much is already saved, and what does that grow to?
* How much needs to be invested every month to get there?
* How much is still missing (the gap)?
* How likely is success, given market uncertainty (Monte Carlo)?

Design notes
------------
* The deterministic FV/PV/SIP math mirrors the legacy ``goal_engine``
  helpers so results are consistent with the existing pipeline, but is
  re-implemented here with full type hints and docstrings.
* Inflation is applied to the *target* for inflation-linked goals and
  the expected return is the *nominal* return used to project the
  corpus.
* The success probability delegates to the seeded Monte Carlo engine so
  results are reproducible.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from wealth_management_system.config import GoalConfig, get_config
from wealth_management_system.exceptions import GoalError
from wealth_management_system.models import Goal, GoalVerdict, UserProfile
from wealth_management_system.models.goal import GoalAnalysis, GoalAnalysisResult
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)


def _years_between(start: date, end: date) -> float:
    """Fractional years between two dates (365.25-day years)."""
    return (end - start).days / 365.25


def _future_value_lump(current: float, annual_return: float, years: float) -> float:
    """Future value of a single lump sum."""
    return current * (1 + annual_return) ** years


def _future_value_sip(monthly: float, annual_return: float, years: float) -> float:
    """Future value of end-of-month SIP contributions.

    Mirrors the legacy ``_project_value`` stream term so results agree
    with the existing goal engine.
    """
    months = max(1, round(years * 12))
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1
    if monthly_rate == 0:
        return monthly * months
    return monthly * (((1 + monthly_rate) ** months - 1) / monthly_rate)


def future_value(
    current_savings: float,
    monthly_contribution: float,
    years: float,
    annual_return: float,
) -> float:
    """Future value of savings plus a monthly SIP stream.

    Parameters
    ----------
    current_savings:
        Lump sum already saved (rupees).
    monthly_contribution:
        Monthly contribution added at end of month (rupees).
    years:
        Investment horizon in years.
    annual_return:
        Nominal annual return (e.g. 0.10 for 10%).

    Returns
    -------
    float
        Projected corpus at the horizon.
    """
    return _future_value_lump(current_savings, annual_return, years) + _future_value_sip(
        monthly_contribution, annual_return, years
    )


def present_value(target: float, annual_return: float, years: float) -> float:
    """Present value of a future target discounted at ``annual_return``."""
    if years <= 0:
        return target
    return target / (1 + annual_return) ** years


def required_sip(
    target_amount: float,
    current_savings: float,
    years: float,
    annual_return: float,
) -> float:
    """Monthly contribution needed to reach ``target_amount``.

    Parameters
    ----------
    target_amount:
        The (inflation-adjusted) goal target in future rupees.
    current_savings:
        Lump sum already saved.
    years:
        Years remaining until the target date.
    annual_return:
        Nominal annual return.

    Returns
    -------
    float
        Monthly SIP required (rupees). 0 if the target is already
        covered by the lump sum's growth.
    """
    months = max(1, round(years * 12))
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    future_lump = _future_value_lump(current_savings, annual_return, years)
    remaining = max(0.0, target_amount - future_lump)

    if remaining == 0:
        return 0.0
    if monthly_rate == 0:
        return remaining / months
    return remaining * monthly_rate / ((1 + monthly_rate) ** months - 1)


class GoalEngine:
    """Analyses every goal for a user into a rich, explained result.

    Parameters
    ----------
    config:
        Optional ``GoalConfig``. Defaults to the process-wide config so
        every engine instance agrees on one set of assumptions.
    simulations:
        Number of Monte Carlo paths for the success probability.
    """

    def __init__(
        self,
        config: Optional[GoalConfig] = None,
        *,
        simulations: int = 10_000,
    ) -> None:
        self._config = config or get_config().goal
        self._simulations = simulations

    # ── public API ──────────────────────────────────────────────────

    def analyse(self, goal: Goal) -> GoalAnalysis:
        """Analyse one goal into a full :class:`GoalAnalysis`.

        Parameters
        ----------
        goal:
            The legacy goal model to analyse.

        Returns
        -------
        GoalAnalysis
            The complete analytical picture.

        Raises
        ------
        GoalError
            If the goal has no target date or a non-positive target.
        """
        if goal.target_date is None:
            raise GoalError(
                "goal must have a target_date",
                code="missing_target_date",
                details={"goal_type": goal.goal_type.value},
            )
        if goal.target_amount <= 0:
            raise GoalError(
                "goal target_amount must be positive",
                code="invalid_target",
                details={"goal_type": goal.goal_type.value, "target": goal.target_amount},
            )

        today = date.today()
        years = max(_years_between(today, goal.target_date), 1 / 12)

        inflation = self._inflation_for(goal)
        expected_return = self._config.default_expected_return

        inflated_target = goal.target_amount * (1 + inflation) ** years
        pv_target = present_value(inflated_target, expected_return, years)
        fv = future_value(
            goal.current_savings_for_goal,
            goal.current_monthly_contribution,
            years,
            expected_return,
        )
        sip = required_sip(inflated_target, goal.current_savings_for_goal, years, expected_return)
        gap = max(0.0, inflated_target - fv)
        progress = min(goal.current_savings_for_goal / inflated_target, 1.0) if inflated_target > 0 else 0.0

        analysis = GoalAnalysis(
            name=goal.notes or goal.goal_type.value.replace("_", " ").title(),
            goal_type=goal.goal_type.value,
            priority=goal.priority.value,
            current_amount=round(goal.current_savings_for_goal, 2),
            target_amount=round(goal.target_amount, 2),
            current_progress=round(progress, 4),
            target_date=goal.target_date,
            years_remaining=round(years, 2),
            inflation_rate=round(inflation, 4),
            expected_return=round(expected_return, 4),
            inflation_adjusted_target=round(inflated_target, 2),
            future_value=round(fv, 2),
            present_value=round(pv_target, 2),
            required_sip=round(sip, 2),
            remaining_gap=round(gap, 2),
        )
        self._attach_probability(analysis, goal, years)
        return analysis

    def analyse_all(self, user: UserProfile) -> GoalAnalysisResult:
        """Analyse every goal of a user.

        Parameters
        ----------
        user:
            The user whose goals should be analysed.

        Returns
        -------
        GoalAnalysisResult
            The aggregate result (one ``GoalAnalysis`` per goal).
        """
        analyses = [self.analyse(g) for g in user.goals]
        return GoalAnalysisResult(goals=analyses)

    def required_sip_total(self, user: UserProfile) -> float:
        """Total monthly SIP required to fund all goals."""
        return self.analyse_all(user).total_required_sip()

    # ── internal helpers ────────────────────────────────────────────

    def _inflation_for(self, goal: Goal) -> float:
        """Pick the inflation rate for a goal.

        Inflation-linked goal types use the default inflation from the
        ``InflationConfig``; everything else is treated as nominal (no
        inflation adjustment).
        """
        inflation_cfg = get_config().inflation
        if goal.goal_type.value in inflation_cfg.inflation_linked_goals:
            return self._config.default_inflation
        return 0.0

    def _attach_probability(
        self, analysis: GoalAnalysis, goal: Goal, years: float
    ) -> None:
        """Populate the Monte Carlo probability and verdict."""
        from wealth_management_system.simulation import MonteCarloEngine

        try:
            engine = MonteCarloEngine(simulations=self._simulations)
            result = engine.run(
                expected_return=analysis.expected_return,
                volatility=self._default_volatility(),
                monthly_investment=goal.current_monthly_contribution,
                inflation=analysis.inflation_rate,
                horizon_years=years,
                initial_corpus=goal.current_savings_for_goal,
                target_amount=analysis.inflation_adjusted_target,
            )
            analysis.expected_corpus = round(result.statistics.median, 2)
            analysis.probability_of_success = round(
                result.statistics.probability_of_success, 4
            )
            analysis.verdict = self._verdict_for(analysis.probability_of_success)
        except Exception as exc:  # pragma: no cover - simulation is defensive
            logger.warning("Monte Carlo probability failed for %s: %s", goal.goal_type, exc)
            analysis.verdict = GoalVerdict.NOT_APPLICABLE

    def _default_volatility(self) -> float:
        """Annual volatility assumption (from the simulation config)."""
        return get_config().simulation.default_volatility

    @staticmethod
    def _verdict_for(probability: Optional[float]) -> GoalVerdict:
        """Map a probability to a plain-language verdict."""
        if probability is None:
            return GoalVerdict.NOT_APPLICABLE
        cfg = get_config().goal
        if probability >= cfg.on_track_threshold:
            return GoalVerdict.ON_TRACK
        if probability >= cfg.at_risk_threshold:
            return GoalVerdict.AT_RISK
        return GoalVerdict.UNLIKELY
