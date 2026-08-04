"""Twin simulation engine.

Drives a twin through a sequence of life events and market returns over
time, producing an evolving timeline. This is the foundation for the
later reinforcement-learning environment: the simulated twin is the
"environment" the RL agent interacts with.
"""

from ml.digital_twin.simulation.engine import TwinSimulationEngine  # noqa: F401

__all__ = ["TwinSimulationEngine"]
