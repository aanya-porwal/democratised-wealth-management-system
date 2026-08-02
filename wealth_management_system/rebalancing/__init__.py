"""Portfolio rebalancing engine.

Detects drift between the current and target allocation, and produces
tax- and cost-aware trade instructions to bring the portfolio back in
line. Designed for long-term investors — rebalancing only triggers when
drift exceeds a configurable threshold.
"""

from wealth_management_system.rebalancing.engine import RebalancingEngine

__all__ = ["RebalancingEngine"]

