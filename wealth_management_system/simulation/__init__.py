"""Simulation package.

* ``monte_carlo`` — a production-grade, vectorised Monte Carlo engine
  (pure logic; plotting lives in ``utilities.plotting``).
* ``scenarios`` — what-if scenario analysis built on the planner.

The simulation engine is deliberately independent of any plotting
library so it can run headless in production.
"""

from wealth_management_system.simulation.monte_carlo import MonteCarloEngine
from wealth_management_system.simulation.scenarios import ScenarioEngine

__all__ = ["MonteCarloEngine", "ScenarioEngine"]
