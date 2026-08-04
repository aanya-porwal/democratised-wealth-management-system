"""Analytics for the Digital Twin Engine.

Computes financial health, net worth, and key financial ratios over a
twin's lifetime. These are deterministic summary metrics (never
replacing the engine's own calculations) that feed the ML feature
engineering and monitoring layers.
"""

from ml.digital_twin.analytics.calculator import (  # noqa: F401
    build_snapshot,
    compute_financial_health,
    compute_financial_ratios,
    net_worth_series,
)

__all__ = [
    "build_snapshot",
    "compute_financial_health",
    "compute_financial_ratios",
    "net_worth_series",
]
