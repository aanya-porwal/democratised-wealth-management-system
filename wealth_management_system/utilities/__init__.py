"""Utilities for the wealth management system.

* ``logging`` — consistent, meaningfully-configured loggers.
* ``plotting`` — optional matplotlib helpers for visualising Monte Carlo
  and allocation results. Plotting is deliberately isolated so the
  simulation engine never depends on a plotting library.
"""

from wealth_management_system.utilities.logging import get_logger, setup_logging
from wealth_management_system.utilities.plotting import (
    plot_allocation,
    plot_simulation_histogram,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "plot_allocation",
    "plot_simulation_histogram",
]
