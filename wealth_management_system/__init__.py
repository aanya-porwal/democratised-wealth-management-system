"""goal-based ai wealth management platform for india.

layered production engine:

legacy engines (backward compatible):
    risk_engine          risk capacity + tolerance
    cashflow_engine      surplus, savings rate, emergency fund
    health_engine        financial health score + plain-language signals
    goal_engine          goal priority, feasibility, surplus allocation
    probability_engine   monte carlo goal success probability
    portfolio_engine     risk score -> target allocation + instruments
    recommendation_engine tax-aware instrument selection
    planner              orchestrates everything into an explained plan

production engine packages:
    config/              typed config.yaml loader (all constants)
    exceptions.py        custom exception hierarchy
    models/              root models.py moved + new engine models
    utilities/           logging + optional plotting helpers
    goals/               goal planning engine (FV, PV, SIP, probability)
    simulation/          monte carlo + scenario analysis engines
    allocation/          strategic allocation engine (12 buckets)
    rebalancing/         drift-aware rebalancing with taxes & costs
    score/               financial health score engine (0-100)
    optimization/        mean-variance optimizer (pluggable)
    recommendation/      explainable recommendation engine
"""

from wealth_management_system.config import get_config
from wealth_management_system.exceptions import WealthManagementError

__all__ = ["get_config", "WealthManagementError"]

