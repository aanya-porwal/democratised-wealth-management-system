"""Portfolio allocation engine.

Produces a strategic target allocation across the full instrument
spectrum (equity, debt, gold, international equity, REITs, fixed
deposits, cash, ELSS, PPF, EPF, NPS, bonds) that varies with the user's
age, risk capacity/tolerance, horizon, liquidity needs, emergency-fund
status and debt burden.
"""

from wealth_management_system.allocation.engine import AllocationEngine

__all__ = ["AllocationEngine"]

