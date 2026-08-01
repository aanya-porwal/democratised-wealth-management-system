"""probability engine — monte carlo success probability for goals.

a single projected number hides the uncertainty. markets do not return
the average every year. this engine simulates thousands of possible
futures, each with a different sequence of returns, and answers the only
question that matters:

"given what this person saves today, how likely is this goal to be met?"

it returns a probability plus the 25th / 75th percentile outcomes so the
plan can talk in ranges, not false precision.
"""

from dataclasses import dataclass

import numpy as np

from wealth_management_system.goal_engine import _project_value
from wealth_management_system.models import Goal

# conservative market assumptions for a blended equity-debt portfolio.
# a 7% mean with 12% volatility understates equity tails on purpose so we
# never over-promise. future: calibrate from actual asset profiles.
DEFAULT_MEAN_RETURN: float = 0.07
DEFAULT_VOLATILITY: float = 0.12
DEFAULT_SIMULATIONS: int = 5000
RNG_SEED: int = 42  # deterministic tests

# percentile outcomes worth reporting to the user
PERCENTILES: tuple = (0.05, 0.25, 0.50, 0.75, 0.95)


@dataclass
class GoalProbability:
    """monte carlo result for one goal."""

    goal_type: str
    target_amount: float
    current_savings: float
    monthly_contribution: float
    years: float
    probability: float  # 0.0 to 1.0
    median_outcome: float  # 50th percentile
    percentile_5: float  # bad case
    percentile_95: float  # good case
    shortfall_median: float  # how short the median path falls
    verdict: str  # on_track / at_risk / unlikely


def _verdict(probability: float) -> str:
    """label a probability so the plan reads in plain language."""
    if probability >= 0.80:
        return "on_track"
    if probability >= 0.50:
        return "at_risk"
    return "unlikely"


def _simulate_paths(
    current_savings: float,
    monthly_contribution: float,
    years: float,
    mean_return: float,
    volatility: float,
    simulations: int,
) -> np.ndarray:
    """simulate ending portfolio values for one goal.

    annual returns are drawn from a lognormal distribution — this keeps
    returns positive in the extreme (prices cannot go below zero) and
    matches how equity markets actually behave.
    """
    months = max(1, round(years * 12))
    monthly_mean = (1 + mean_return) ** (1 / 12) - 1
    monthly_vol = volatility / (12**0.5)

    rng = np.random.default_rng(RNG_SEED)

    # random annual-ish returns, vectorised across all simulations
    # simulate monthly to line up with monthly contributions
    # shape: (simulations, months)
    returns = rng.lognormal(
        mean=np.log1p(monthly_mean) - 0.5 * monthly_vol**2,
        sigma=monthly_vol,
        size=(simulations, months),
    )

    # cumulative growth of the initial lump sum over the full period
    lump_growth = returns.prod(axis=1)

    # growth factor for each monthly contribution at its deposit month:
    # contribution at month m grows for (months - m) periods
    # we build weights via cumulative products reversed
    reversed_prod = np.flip(np.cumprod(np.flip(returns, axis=1), axis=1), axis=1)
    # contribution at month 0 (first deposit) grows for all months:
    # its weight is reversed_prod[..., 0]... but we deposit at END of month,
    # so first deposit grows for (months-1) periods.
    # simpler: shift weights so deposit at month m uses reversed_prod[..., m+1:]
    weights = np.ones_like(returns)
    weights[:, :-1] = reversed_prod[:, 1:]
    weights[:, -1] = 1.0  # last deposit earns nothing

    contributions_fv = monthly_contribution * weights.sum(axis=1)

    return current_savings * lump_growth + contributions_fv


def simulate_goal_probability(
    goal: Goal,
    mean_return: float = DEFAULT_MEAN_RETURN,
    volatility: float = DEFAULT_VOLATILITY,
    simulations: int = DEFAULT_SIMULATIONS,
) -> GoalProbability:
    """run the monte carlo for a single goal."""
    years = max(goal.years_to_goal(), 1 / 12)

    paths = _simulate_paths(
        goal.current_savings_for_goal,
        goal.current_monthly_contribution,
        years,
        mean_return,
        volatility,
        simulations,
    )

    probability = float(np.mean(paths >= goal.target_amount))

    pcts = np.percentile(paths, PERCENTILES)
    median = float(pcts[2])

    return GoalProbability(
        goal_type=goal.goal_type.value,
        target_amount=goal.target_amount,
        current_savings=goal.current_savings_for_goal,
        monthly_contribution=goal.current_monthly_contribution,
        years=round(years, 2),
        probability=round(probability, 4),
        median_outcome=round(median),
        percentile_5=round(float(pcts[0])),
        percentile_95=round(float(pcts[4])),
        shortfall_median=round(max(0.0, goal.target_amount - median)),
        verdict=_verdict(probability),
    )


def project_future_value(
    current_savings: float,
    monthly_contribution: float,
    years: float,
    annual_return: float = DEFAULT_MEAN_RETURN,
) -> float:
    """deterministic future value used by the planner for quick math."""
    return round(_project_value(current_savings, monthly_contribution, years, annual_return))

