"""Scenario analysis models.

A ``Scenario`` describes a "what-if" adjustment applied to a user's
financial inputs so the planner can recompute goals, SIP, net worth and
allocation under different futures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ScenarioType(str, Enum):
    """The kind of scenario being modelled."""

    SALARY_INCREASE = "salary_increase"
    SALARY_DECREASE = "salary_decrease"
    MARKET_CRASH = "market_crash"
    EARLY_RETIREMENT = "early_retirement"
    DELAYED_RETIREMENT = "delayed_retirement"
    HOUSE_PURCHASE = "house_purchase"
    CHILD_EDUCATION = "child_education"
    MARRIAGE = "marriage"
    EMERGENCY_EXPENSE = "emergency_expense"


@dataclass
class Scenario:
    """A single what-if scenario.

    Attributes
    ----------
    scenario_type:
        The scenario kind.
    name:
        Human-readable name (defaults to the type's value).
    description:
        Longer plain-language description.
    income_multiplier:
        Optional multiplier on monthly income (1.15 = +15%).
    expense_multiplier:
        Optional multiplier on monthly expenses (1.05 = +5%).
    portfolio_drawdown:
        Optional immediate portfolio drawdown (0.30 = -30%).
    one_time_expense:
        Optional one-off rupee expense (e.g. a house down-payment).
    monthly_contribution_adjustment:
        Optional absolute change in monthly investment (rupees).
    emergency_fund_months:
        Optional new emergency-fund coverage in months.
    retirement_age:
        Optional new retirement age (for early/delayed retirement).
    target_date_shift_years:
        Optional shift applied to every goal's target date (years).
    """

    scenario_type: ScenarioType
    name: str = ""
    description: str = ""
    income_multiplier: Optional[float] = None
    expense_multiplier: Optional[float] = None
    portfolio_drawdown: Optional[float] = None
    one_time_expense: Optional[float] = None
    monthly_contribution_adjustment: Optional[float] = None
    emergency_fund_months: Optional[float] = None
    retirement_age: Optional[int] = None
    target_date_shift_years: Optional[float] = None

    def __post_init__(self) -> None:
        """Fill the display name if not provided."""
        if not self.name:
            self.name = self.scenario_type.value.replace("_", " ").title()


@dataclass
class ScenarioVariant:
    """A scenario applied to a user, with the recomputed metrics.

    Attributes
    ----------
    scenario:
        The scenario definition.
    goal_probabilities:
        Per-goal success probability under the scenario.
    total_required_sip:
        Total monthly SIP required across goals under the scenario.
    net_worth:
        Net worth under the scenario.
    allocation:
        Strategic allocation under the scenario (bucket -> weight).
    summary:
        Plain-language summary of the scenario's impact.
    """

    scenario: Scenario
    goal_probabilities: dict[str, float] = field(default_factory=dict)
    total_required_sip: float = 0.0
    net_worth: float = 0.0
    allocation: dict[str, float] = field(default_factory=dict)
    summary: str = ""
