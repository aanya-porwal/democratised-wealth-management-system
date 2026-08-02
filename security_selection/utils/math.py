"""Small numeric utilities used across the platform."""

from __future__ import annotations

from typing import Any


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp ``value`` into ``[lo, hi]``."""
    return max(lo, min(hi, value))


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Convert to float, returning ``default`` on failure (never raise)."""
    try:
        if value is None:
            return default
        result = float(value)
        if result != result:  # NaN
            return default
        return result
    except (TypeError, ValueError):
        return default


def safe_divide(numerator: float, denominator: float, default: float | None = None) -> float | None:
    """Divide guarding against zero/None denominators."""
    if denominator is None or abs(denominator) < 1e-12:
        return default
    return numerator / denominator


def winsorize(values: list[float], limits: tuple[float, float] = (0.01, 0.01)) -> list[float]:
    """Cap extreme values at the given quantiles (robust to outliers)."""
    if not values:
        return []
    ordered = sorted(values)
    n = len(ordered)
    lo_idx = max(0, int(n * limits[0]))
    hi_idx = min(n - 1, n - 1 - int(n * limits[1]))
    lo, hi = ordered[lo_idx], ordered[hi_idx]
    return [max(lo, min(hi, v)) for v in values]

