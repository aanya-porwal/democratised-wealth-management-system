"""goal engine — feasibility, priority and surplus allocation.

the planner must answer three questions about every goal:

1. can this goal be met on the current path? (feasibility)
2. which goals get money first when surplus is limited? (priority)
3. how should the available surplus be split? (allocation)

the golden rule encoded here: cashflow and emergency fund come before
any long-term goal. a goal that needs money in 3 years should never be
funded with a product designed for 15 years.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from wealth_management_system.cashflow_engine import (
    build_cashflow_snapshot,
    emergency_fund_allocation,
)
from wealth_management_system.models import Goal, GoalPriority, UserProfile

# conservative real return assumption used for goal projections.
# future: replace fixed return with a monte carlo distribution.
DEFAULT_REAL_RETURN: float = 0.07

# debt is expensive; goals funded with borrowed money are less attractive
DEBT_INTEREST_RATE: float = 0.12

# a goal with under 60% probability of being met on the current path
# needs the plan to change (contribute more, extend the date, or lower
# the target). keep the threshold visible so it is easy to tune.
FEASIBILITY_THRESHOLD: float = 0.60


@dataclass
class GoalFeasibility:
    """how likely a goal is on the current savings path."""

    goal_type: str
    priority: str
    target_amount: float
    current_savings: float
    monthly_contribution: float  # already being saved each month
    years: float
    projected_value: float
    probability: float  # 0.0 to 1.0
    required_monthly: float  # what would be needed to hit the target
    shortfall: float  # projected vs target, positive = short
    feasible: bool


@dataclass
class GoalAllocation:
    """one goal's share of the monthly surplus."""

    goal_type: str
    priority: str
    allocated: float  # monthly rupees
    reason: str


@dataclass
class GoalPlan:
    """the complete goal layer: feasibility plus allocation."""

    goals: List[GoalFeasibility] = field(default_factory=list)
    allocations: List[GoalAllocation] = field(default_factory=list)
    surplus_after_foundations: float = 0.0
    fully_funded: bool = True
    notes: List[str] = field(default_factory=list)


def _project_value(
    current_savings: float,
    monthly_contribution: float,
    years: float,
    annual_return: float,
) -> float:
    """future value of savings + monthly contributions.

    monthly contributions are added at the end of each month (annuity due
    at month end, matching how SIPs work in practice).
    """
    months = max(1, round(years * 12))
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    # future value of the lump sum already saved
    lump = current_savings * (1 + annual_return) ** years
    # future value of a monthly stream
    if monthly_rate != 0:
        stream = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        stream = monthly_contribution * months
    return lump + stream


def assess_goal_feasibility(
    goal: Goal, annual_return: float = DEFAULT_REAL_RETURN
) -> GoalFeasibility:
    """evaluate a single goal on its current savings path."""
    years = max(goal.years_to_goal(), 1 / 12)

    # future value of what they are already doing
    projected = _project_value(
        goal.current_savings_for_goal,
        goal.current_monthly_contribution,
        years,
        annual_return,
    )

    # what monthly contribution would exactly meet the target?
    required = _required_monthly(
        goal.target_amount, goal.current_savings_for_goal, years, annual_return
    )

    # simple feasibility proxy: how much of the target is covered.
    # future: drive this from the monte carlo probability engine.
    coverage = projected / goal.target_amount if goal.target_amount > 0 else 1.0
    probability = min(coverage, 1.0)

    return GoalFeasibility(
        goal_type=goal.goal_type.value,
        priority=goal.priority.value,
        target_amount=goal.target_amount,
        current_savings=goal.current_savings_for_goal,
        monthly_contribution=goal.current_monthly_contribution,
        years=round(years, 2),
        projected_value=round(projected),
        probability=round(probability, 4),
        required_monthly=round(required),
        shortfall=round(max(0.0, goal.target_amount - projected)),
        feasible=probability >= FEASIBILITY_THRESHOLD,
    )


def _required_monthly(
    target_amount: float,
    current_savings: float,
    years: float,
    annual_return: float,
) -> float:
    """monthly contribution needed to reach a target from current savings."""
    months = max(1, round(years * 12))
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    # what the current lump grows to — that portion is already covered
    future_lump = current_savings * (1 + annual_return) ** years
    remaining = max(0.0, target_amount - future_lump)

    if remaining == 0:
        return 0.0
    if monthly_rate == 0:
        return remaining / months
    return remaining * monthly_rate / ((1 + monthly_rate) ** months - 1)


def rank_goals_by_priority(user: UserProfile) -> List[Goal]:
    """order goals by priority, then by soonest target date."""
    order = {GoalPriority.CRITICAL: 0, GoalPriority.HIGH: 1, GoalPriority.ASPIRATIONAL: 2}
    return sorted(user.goals, key=lambda g: (order[g.priority], g.target_date))


def allocate_surplus(
    user: UserProfile,
    discretionary_surplus: float,
    goals: List[Goal] | None = None,
) -> List[GoalAllocation]:
    """allocate surplus to goals in strict priority order.

    rules:
    * emergency fund gets a share first (it is the foundation)
    * remaining surplus flows to the highest-priority goals first
    * once a goal is fully funded, the next goal gets the money
    * if money runs out, lower-priority goals are left unfunded and the
      plan will say so explicitly.
    """
    if goals is None:
        goals = user.goals

    ordered = rank_goals_by_priority(user)
    ordered = [g for g in ordered if g.goal_type.value != "emergency_fund"]
    # if no goals remain after removing emergency fund, return empty
    if not ordered:
        return []

    # hold back the emergency fund share first
    snapshot = build_cashflow_snapshot(user)
    ef_share = emergency_fund_allocation(user, snapshot)
    remaining = max(0.0, discretionary_surplus - ef_share)

    allocations: List[GoalAllocation] = []
    for goal in ordered:
        if remaining <= 0:
            allocations.append(
                GoalAllocation(
                    goal_type=goal.goal_type.value,
                    priority=goal.priority.value,
                    allocated=0.0,
                    reason="no surplus left after higher-priority goals",
                )
            )
            continue

        # monthly need to hit the target on time
        need = _required_monthly(
            goal.target_amount,
            goal.current_savings_for_goal,
            max(goal.years_to_goal(), 1 / 12),
            DEFAULT_REAL_RETURN,
        )
        # gap between what they already save and what the goal needs
        gap = max(0.0, need - goal.current_monthly_contribution)
        if gap <= 0:
            allocations.append(
                GoalAllocation(
                    goal_type=goal.goal_type.value,
                    priority=goal.priority.value,
                    allocated=0.0,
                    reason="already on track (current contribution covers the need)",
                )
            )
            continue

        to_goal = min(remaining, gap)
        remaining -= to_goal
        allocations.append(
            GoalAllocation(
                goal_type=goal.goal_type.value,
                priority=goal.priority.value,
                allocated=round(to_goal),
                reason=f"closes the gap to the required ₹{need:,.0f}/month",
            )
        )

    return allocations


def build_goal_plan(user: UserProfile) -> GoalPlan:
    """build the full goal layer: feasibility, priority, allocation."""
    snapshot = build_cashflow_snapshot(user)

    # feasibility for every goal on the current path
    feasibilities = [assess_goal_feasibility(g) for g in user.goals]

    # allocations from the discretionary surplus after foundations
    allocations = allocate_surplus(user, snapshot.discretionary_surplus)

    any_unfunded = any(a.allocated == 0 and a.reason.startswith("no surplus") for a in allocations)
    fully_funded = not any_unfunded

    notes = []
    if snapshot.emergency_fund_priority != "ready":
        notes.append(
            "emergency fund takes priority — long-term goals only get "
            "what is left after the buffer is built"
        )
    if not fully_funded:
        notes.append(
            "surplus is exhausted before every goal is covered — lower-priority "
            "goals will need more income, a later date, or a smaller target"
        )

    return GoalPlan(
        goals=feasibilities,
        allocations=allocations,
        surplus_after_foundations=snapshot.discretionary_surplus,
        fully_funded=fully_funded,
        notes=notes,
    )

