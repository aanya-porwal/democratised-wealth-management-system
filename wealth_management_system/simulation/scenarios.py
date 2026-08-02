"""Scenario analysis engine.

Models "what-if" futures — a salary increase, a market crash, early
retirement, a house purchase, child education, a marriage, an emergency
expense — and recomputes the metrics that matter:

* goal success probability
* required monthly SIP
* net worth
* asset allocation

Each :class:`Scenario` is a set of multiplicative/absolute adjustments
applied to a *copy* of the user, so the original profile is never
mutated. The engine reuses the goal engine, the allocation engine and
the Monte Carlo engine so results are consistent with the rest of the
system.
"""

from __future__ import annotations

import logging
import copy
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional

from wealth_management_system.allocation import AllocationEngine
from wealth_management_system.config import ScenarioConfig, get_config
from wealth_management_system.exceptions import SimulationError
from wealth_management_system.goals import GoalEngine
from wealth_management_system.models import (
    AllocationEngineInput,
    Scenario,
    ScenarioType,
    ScenarioVariant,
    UserProfile,
)
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)


class ScenarioEngine:
    """Applies a scenario to a user and recomputes the plan metrics.

    Parameters
    ----------
    config:
        Optional ``ScenarioConfig`` for default severities.
    simulations:
        Number of Monte Carlo paths used for goal probabilities.
    """

    def __init__(
        self,
        config: Optional[ScenarioConfig] = None,
        *,
        simulations: int = 10_000,
    ) -> None:
        self._config = config or get_config().scenario
        self._simulations = simulations
        self._goals = GoalEngine(simulations=simulations)
        self._allocation = AllocationEngine()

    # ── public API ──────────────────────────────────────────────────

    def apply(self, user: UserProfile, scenario: Scenario) -> ScenarioVariant:
        """Apply a scenario to a user and recompute the key metrics.

        Parameters
        ----------
        user:
            The original user (never mutated).
        scenario:
            The what-if scenario to apply.

        Returns
        -------
        ScenarioVariant
            Recalculated goal probabilities, total required SIP, net
            worth, asset allocation and a plain-language summary.

        Raises
        ------
        SimulationError
            If the scenario has no adjustments at all.
        """
        if not self._has_adjustments(scenario):
            raise SimulationError(
                "scenario has no adjustments",
                code="empty_scenario",
                details={"scenario": scenario.scenario_type.value},
            )

        adjusted = self._apply_to_user(user, scenario)

        # goal probabilities under the scenario
        goal_result = self._goals.analyse_all(adjusted)
        probabilities: Dict[str, float] = {}
        for analysis in goal_result.goals:
            probabilities[analysis.goal_type] = analysis.probability_of_success or 0.0

        total_sip = goal_result.total_required_sip()
        net_worth = adjusted.financial.net_worth()

        allocation = self._allocation.build(AllocationEngineInput(user=adjusted))
        allocation_map = allocation.as_dict()

        summary = self._summarise(scenario, probabilities, total_sip, net_worth)

        return ScenarioVariant(
            scenario=scenario,
            goal_probabilities=probabilities,
            total_required_sip=round(total_sip, 2),
            net_worth=round(net_worth, 2),
            allocation=allocation_map,
            summary=summary,
        )

    def apply_preset(
        self, user: UserProfile, scenario_type: ScenarioType
    ) -> ScenarioVariant:
        """Apply a preset scenario with config-derived defaults.

        Parameters
        ----------
        user:
            The original user.
        scenario_type:
            The kind of scenario to model (salary increase, market
            crash, early retirement, ...).

        Returns
        -------
        ScenarioVariant
            The recomputed metrics under the preset scenario.
        """
        scenario = self._preset(scenario_type, user)
        return self.apply(user, scenario)

    def compare(
        self, user: UserProfile, scenarios: List[Scenario]
    ) -> List[ScenarioVariant]:
        """Apply several scenarios and return all variants.

        The first variant (index 0) is the baseline (no adjustments) so
        callers can compare every scenario against "no change".
        """
        baseline = Scenario(
            scenario_type=ScenarioType.EMERGENCY_EXPENSE,
            name="Baseline",
            description="No change — the user's current path.",
            income_multiplier=1.0,
            expense_multiplier=1.0,
        )
        variants = [self.apply(user, baseline)]
        variants.extend(self.apply(user, s) for s in scenarios)
        return variants

    # ── preset scenarios ────────────────────────────────────────────

    def _preset(self, scenario_type: ScenarioType, user: UserProfile) -> Scenario:
        """Build a preset scenario using config defaults."""
        cfg = self._config
        monthly_income = user.financial.monthly_income
        monthly_expenses = (
            user.financial.monthly_fixed_expenses + user.financial.monthly_variable_expenses
        )

        if scenario_type == ScenarioType.SALARY_INCREASE:
            return Scenario(
                scenario_type=scenario_type,
                income_multiplier=1.0 + cfg.salary_increase_pct,
                description=f"Salary rises {cfg.salary_increase_pct:.0%}",
            )
        if scenario_type == ScenarioType.SALARY_DECREASE:
            return Scenario(
                scenario_type=scenario_type,
                income_multiplier=1.0 - cfg.salary_decrease_pct,
                description=f"Salary falls {cfg.salary_decrease_pct:.0%}",
            )
        if scenario_type == ScenarioType.MARKET_CRASH:
            return Scenario(
                scenario_type=scenario_type,
                portfolio_drawdown=cfg.market_crash_drawdown,
                description=f"Market crashes {cfg.market_crash_drawdown:.0%}",
            )
        if scenario_type == ScenarioType.EARLY_RETIREMENT:
            return Scenario(
                scenario_type=scenario_type,
                retirement_age=max(user.age + 1, 50),
                description="Retire earlier than planned",
            )
        if scenario_type == ScenarioType.DELAYED_RETIREMENT:
            return Scenario(
                scenario_type=scenario_type,
                retirement_age=user.years_to_retirement() + 65,
                description="Retire later than planned",
            )
        if scenario_type == ScenarioType.HOUSE_PURCHASE:
            return Scenario(
                scenario_type=scenario_type,
                one_time_expense=max(monthly_income * 24, 500000),
                description="Buying a home — one-time outflow",
            )
        if scenario_type == ScenarioType.CHILD_EDUCATION:
            return Scenario(
                scenario_type=scenario_type,
                one_time_expense=max(monthly_income * 36, 1000000),
                monthly_contribution_adjustment=-max(monthly_income * 0.1, 2000),
                description="Child education — higher expenses and a new goal",
            )
        if scenario_type == ScenarioType.MARRIAGE:
            return Scenario(
                scenario_type=scenario_type,
                one_time_expense=max(monthly_income * 12, 300000),
                description="Marriage — one-time outflow",
            )
        if scenario_type == ScenarioType.EMERGENCY_EXPENSE:
            return Scenario(
                scenario_type=scenario_type,
                one_time_expense=monthly_expenses * cfg.emergency_expense_months,
                description="Unexpected emergency expense",
            )
        # fallback — no adjustments
        return Scenario(
            scenario_type=scenario_type,
            description="Custom scenario (no preset defaults)",
        )

    # ── applying adjustments ────────────────────────────────────────

    @staticmethod
    def _has_adjustments(scenario: Scenario) -> bool:
        """Whether the scenario actually changes anything."""
        return any(
            value is not None
            for value in (
                scenario.income_multiplier,
                scenario.expense_multiplier,
                scenario.portfolio_drawdown,
                scenario.one_time_expense,
                scenario.monthly_contribution_adjustment,
                scenario.emergency_fund_months,
                scenario.retirement_age,
                scenario.target_date_shift_years,
            )
        )

    def _apply_to_user(self, user: UserProfile, scenario: Scenario) -> UserProfile:
        """Produce a deep-copied, scenario-adjusted user profile."""
        adjusted = copy.deepcopy(user)
        financial = adjusted.financial

        # income & expenses
        if scenario.income_multiplier is not None:
            old_income = financial.monthly_income + financial.secondary_monthly_income
            financial.monthly_income = max(
                0.0, financial.monthly_income * scenario.income_multiplier
            )
            financial.secondary_monthly_income = max(
                0.0, financial.secondary_monthly_income * scenario.income_multiplier
            )
            # a change in income changes how much the user can invest each
            # month — scale every goal's current contribution proportionally
            # so the recalculated probabilities respond to the scenario.
            new_income = financial.monthly_income + financial.secondary_monthly_income
            if old_income > 0:
                multiplier = new_income / old_income
                for goal in adjusted.goals:
                    goal.current_monthly_contribution = max(
                        0.0, goal.current_monthly_contribution * multiplier
                    )
        if scenario.expense_multiplier is not None:
            financial.monthly_fixed_expenses = max(
                0.0, financial.monthly_fixed_expenses * scenario.expense_multiplier
            )
            financial.monthly_variable_expenses = max(
                0.0, financial.monthly_variable_expenses * scenario.expense_multiplier
            )

        # portfolio drawdown reduces existing investments
        if scenario.portfolio_drawdown is not None:
            financial.existing_investments *= max(0.0, 1.0 - scenario.portfolio_drawdown)
            financial.gold_value *= max(0.0, 1.0 - scenario.portfolio_drawdown * 0.5)

        # one-time expense reduces liquid assets / increases debt
        if scenario.one_time_expense is not None:
            expense = scenario.one_time_expense
            absorbed = min(financial.existing_investments, expense)
            financial.existing_investments -= absorbed
            remaining = expense - absorbed
            if remaining > 0:
                financial.total_debt += remaining
                financial.monthly_emi_total += remaining / 120  # ~10yr repayment

        # monthly contribution adjustment
        if scenario.monthly_contribution_adjustment is not None:
            financial.existing_monthly_sip = max(
                0.0,
                financial.existing_monthly_sip + scenario.monthly_contribution_adjustment,
            )

        # emergency fund months override
        if scenario.emergency_fund_months is not None:
            financial.emergency_fund_months = scenario.emergency_fund_months

        # target date shift for all goals
        if scenario.target_date_shift_years is not None:
            delta = timedelta(days=round(scenario.target_date_shift_years * 365.25))
            for goal in adjusted.goals:
                goal.target_date = goal.target_date + delta

        return adjusted

    # ── summary ─────────────────────────────────────────────────────

    @staticmethod
    def _summarise(
        scenario: Scenario,
        probabilities: Dict[str, float],
        total_sip: float,
        net_worth: float,
    ) -> str:
        """Plain-language summary of the scenario's impact."""
        if not probabilities:
            prob_part = "no goals to evaluate"
        else:
            avg = sum(probabilities.values()) / len(probabilities)
            prob_part = f"average goal probability {avg:.0%}"
        return (
            f"{scenario.name}: {prob_part}, total required SIP "
            f"₹{total_sip:,.0f}/mo, net worth ₹{net_worth:,.0f}"
        )

