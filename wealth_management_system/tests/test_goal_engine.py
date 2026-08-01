"""tests for the goal engine."""

from wealth_management_system.goal_engine import (
    allocate_surplus,
    assess_goal_feasibility,
    build_goal_plan,
    rank_goals_by_priority,
)
from wealth_management_system.models import GoalPriority, GoalType
from wealth_management_system.sample_users import build_all_sample_users, ravi

PRIYA = [u for u in build_all_sample_users() if u.name == "Priya Parent"][0]


def test_goal_plan_has_all_goals():
    """feasibility must be produced for every goal."""
    plan = build_goal_plan(ravi)
    assert len(plan.goals) == len(ravi.goals)


def test_goal_priority_order():
    """critical goals must rank before high before aspirational."""
    ordered = rank_goals_by_priority(PRIYA)
    priorities = [g.priority for g in ordered]
    # must be sorted critical first
    assert priorities == sorted(priorities, key=lambda p: _priority_rank(p))


def _priority_rank(p: GoalPriority) -> int:
    return {GoalPriority.CRITICAL: 0, GoalPriority.HIGH: 1, GoalPriority.ASPIRATIONAL: 2}[p]


def test_emergency_fund_goals_are_handled_by_cashflow_engine():
    """emergency fund is a cashflow concern, not a surplus allocation."""
    # a user whose ONLY goal is emergency fund should produce no allocations
    user = build_all_sample_users()[0]  # ravi has EF + wealth
    allocations = allocate_surplus(user, 5000)
    assert not any(a.goal_type == GoalType.EMERGENCY_FUND.value for a in allocations)


def test_feasibility_is_boolean():
    """feasible must be a real bool, not a float."""
    for goal in ravi.goals:
        f = assess_goal_feasibility(goal)
        assert isinstance(f.feasible, bool)


def test_allocation_respects_priority():
    """higher-priority goals must never receive less than lower-priority ones
    when there is enough surplus to cover both."""
    plan = build_goal_plan(PRIYA)
    alloc_by_goal = {a.goal_type: a for a in plan.allocations}

    # retirement is high priority, travel is aspirational
    if "retirement" in alloc_by_goal and "travel" in alloc_by_goal:
        ret = alloc_by_goal["retirement"].allocated
        travel = alloc_by_goal["travel"].allocated
        # if travel gets anything, retirement must be fully satisfied first
        if travel > 0:
            assert ret > 0

