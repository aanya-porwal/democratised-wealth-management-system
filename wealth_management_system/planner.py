"""planner — orchestrates every engine into one explained financial plan.

this is the system's brain. it runs the full financial-planning flow in
the order a certified planner would:

1. cashflow      -> what money exists each month
2. health        -> how healthy the foundations are
3. goals         -> what the money is for, and whether it is realistic
4. risk          -> how much risk the user can take
5. portfolio     -> what the allocation should look like
6. probability   -> how likely each goal actually is

every output is paired with a plain-language reason, because a number a
user cannot understand will never change their behaviour.
"""

from dataclasses import dataclass, field
from typing import List

from wealth_management_system.cashflow_engine import (
    CashflowSnapshot,
    build_cashflow_snapshot,
    emergency_fund_allocation,
)
from wealth_management_system.goal_engine import GoalPlan, build_goal_plan
from wealth_management_system.health_engine import (
    FinancialHealth,
    assess_health,
)
from wealth_management_system.models import Goal, UserProfile
from wealth_management_system.portfolio_engine import (
    PortfolioPlan,
    build_portfolio,
)
from wealth_management_system.probability_engine import (
    GoalProbability,
    simulate_goal_probability,
)
from wealth_management_system.risk_engine import RiskAssessment, assess_risk


@dataclass
class Action:
    """a single recommended action with a justification."""

    action: str  # what to do
    reason: str  # why now, why this
    priority: str  # now / next / later


@dataclass
class FinancialPlan:
    """the complete, explained plan for one user."""

    user_name: str
    summary: str
    cashflow: CashflowSnapshot
    health: FinancialHealth
    goals: GoalPlan
    risk: RiskAssessment
    portfolio: PortfolioPlan
    probabilities: List[GoalProbability] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)


def _emergency_fund_monthly_target(user: UserProfile, cash: CashflowSnapshot) -> float:
    """rupees per month to complete the emergency fund on a 12-month plan."""
    if cash.emergency_fund_priority == "ready":
        return 0.0
    # spread the gap over 12 months so the goal is concrete
    return max(cash.emergency_fund_amount_needed / 12, 0.0)


def _build_actions(
    user: UserProfile,
    cash: CashflowSnapshot,
    health: FinancialHealth,
    goal_plan: GoalPlan,
    probabilities: List[GoalProbability],
) -> List[Action]:
    """turn engine outputs into ordered, explained actions."""
    actions: List[Action] = []
    financial = user.financial

    # 1. cashflow — overspending kills every plan
    if cash.monthly_surplus <= 0:
        actions.append(
            Action(
                "cut expenses or raise income before investing anything",
                "spending already exceeds income — no surplus exists to invest",
                "now",
            )
        )

    # 2. emergency fund — the foundation
    if cash.emergency_fund_priority == "missing":
        actions.append(
            Action(
                f"build an emergency fund of ₹{cash.emergency_fund_amount_needed:,.0f} "
                f"(about ₹{_emergency_fund_monthly_target(user, cash):,.0f}/month)",
                "no buffer exists — one shock forces debt or selling investments early",
                "now",
            )
        )
    elif cash.emergency_fund_priority == "building":
        actions.append(
            Action(
                f"top up the emergency fund to {cash.emergency_fund_target_months:.0f} months "
                f"(₹{cash.emergency_fund_amount_needed:,.0f} more)",
                "the buffer is partial; finish it before heavy long-term investing",
                "now",
            )
        )

    # 3. high-interest debt — expensive, kills compounding
    if financial.debt_to_income_ratio() > 0.35:
        actions.append(
            Action(
                "clear high-interest debt before investing aggressively",
                f"debt consumes {financial.debt_to_income_ratio():.0%} of income — "
                "no investment reliably beats a 12%+ loan",
                "now",
            )
        )

    # 4. protection — dependents cannot be left exposed
    needs = []
    if not financial.has_health_insurance:
        needs.append("health insurance")
    if user.dependents > 0 and not financial.has_term_life_insurance:
        needs.append("term life cover")
    if needs:
        actions.append(
            Action(
                "get " + " and ".join(needs),
                "protection comes before accumulation — a medical or income shock "
                "would erase years of investing",
                "now" if user.dependents > 0 else "next",
            )
        )

    # 5. goals — the ones that need attention
    for p in probabilities:
        if p.verdict == "unlikely":
            actions.append(
                Action(
                    f"revisit the {p.goal_type.replace('_', ' ')} goal — increase the "
                    f"monthly contribution or extend the date",
                    f"only a {p.probability:.0%} chance of success on the current path "
                    f"(median shortfall ₹{p.shortfall_median:,.0f})",
                    "next",
                )
            )
        elif p.verdict == "at_risk":
            actions.append(
                Action(
                    f"keep funding the {p.goal_type.replace('_', ' ')} goal, ideally a "
                    "little more each month",
                    f"{p.probability:.0%} probability is workable but fragile",
                    "next",
                )
            )

    # 6. idle money — cash beyond the emergency fund should be working
    if cash.emergency_fund_priority == "ready" and financial.existing_investments == 0:
        actions.append(
            Action(
                "start investing the surplus",
                "emergency fund is complete and no investments exist — "
                "money is sitting idle and losing to inflation",
                "next",
            )
        )

    # 7. portfolio — start investing once foundations are in place
    if cash.emergency_fund_priority == "ready" and financial.debt_to_income_ratio() <= 0.35:
        actions.append(
            Action(
                f"invest around {goal_plan.surplus_after_foundations:,.0f}/month into the "
                "suggested allocation",
                "foundations are in place — surplus should now work toward the goals",
                "next",
            )
        )

    return actions


def build_plan(user: UserProfile, years: float = 7.0) -> FinancialPlan:
    """run the whole planning pipeline for one user."""
    cash = build_cashflow_snapshot(user)
    health = assess_health(user)
    goal_plan = build_goal_plan(user)
    risk = assess_risk(user)
    portfolio = build_portfolio(user, years=years)

    probabilities = [simulate_goal_probability(g) for g in user.goals]
    actions = _build_actions(user, cash, health, goal_plan, probabilities)

    summary = (
        f"{user.name}'s foundations are {health.grade} (health {health.score}/100). "
        f"Risk capacity: {risk.risk_category.lower()} ({risk.final_score_100}/100). "
        f"{_summarise_goals(probabilities)}"
    )

    return FinancialPlan(
        user_name=user.name,
        summary=summary,
        cashflow=cash,
        health=health,
        goals=goal_plan,
        risk=risk,
        portfolio=portfolio,
        probabilities=probabilities,
        actions=actions,
    )


def _summarise_goals(probabilities: List[GoalProbability]) -> str:
    """one-line plain-language summary of the goal outlook."""
    if not probabilities:
        return "no goals defined."
    on_track = sum(1 for p in probabilities if p.verdict == "on_track")
    at_risk = sum(1 for p in probabilities if p.verdict == "at_risk")
    unlikely = sum(1 for p in probabilities if p.verdict == "unlikely")
    bits = []
    if on_track:
        bits.append(f"{on_track} goal(s) on track")
    if at_risk:
        bits.append(f"{at_risk} goal(s) at risk")
    if unlikely:
        bits.append(f"{unlikely} goal(s) unlikely on the current path")
    return "Goal outlook: " + ", ".join(bits) + "." if bits else ""

