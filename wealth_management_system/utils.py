"""Shared helper functions and small constants.

Contains the general-purpose utilities used across the package:

* ``elss_irr`` — IRR-based effective return for ELSS (was referenced by
  the original notebook but never defined; implemented here to keep the
  tax-aware recommendation pipeline working).
* ``format_inr`` — consistent Rupee formatting used by demos.
"""

import sys
from typing import List

# ─────────────────────────────────────────────────────────────────────
# Console helper
# ─────────────────────────────────────────────────────────────────────


def ensure_utf8_console() -> None:
    """Reconfigure stdout/stderr for UTF-8 so the rupee symbol prints on Windows.

    Windows consoles default to cp1252 which cannot encode the ₹ glyph.
    Called from the demo entry points (main, tests) so every printed rupee
    survives on a fresh terminal.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass  # not a text stream or already configured


# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

ELSS_LOCK_IN_YEARS: float = 3.0
EQUITY_LTCG_RATE: float = 0.10  # long-term capital gains tax rate
SGB_INTEREST_RATE: float = 0.025  # sovereign gold bond annual interest

# ─────────────────────────────────────────────────────────────────────
# Money formatting
# ─────────────────────────────────────────────────────────────────────


def format_inr(value: float) -> str:
    """Format a number as Indian Rupees, e.g. ``₹1,80,000``."""
    return f"₹{value:,.0f}"


# ─────────────────────────────────────────────────────────────────────
# Financial math (IRR helpers)
# ─────────────────────────────────────────────────────────────────────


def net_present_value(rate: float, cashflows: List[float]) -> float:
    """NPV of a series of (monthly) cash flows at a monthly discount rate."""
    return sum(cf / (1 + rate) ** i for i, cf in enumerate(cashflows))


def internal_rate_of_return(
    cashflows: List[float],
    lower: float = -0.999,
    upper: float = 10.0,
    tolerance: float = 1e-9,
    max_iterations: int = 500,
) -> float:
    """Bisection search for the rate that makes the NPV of ``cashflows`` zero.

    ``lower``/``upper`` are monthly rates. If no sign change is found the
    function falls back to the bound closest to zero — this keeps the
    behaviour deterministic for pathological input.
    """
    npv_lower = net_present_value(lower, cashflows)
    npv_upper = net_present_value(upper, cashflows)

    if abs(npv_lower) < tolerance:
        return lower
    if abs(npv_upper) < tolerance:
        return upper

    if npv_lower * npv_upper > 0:
        # No sign change: no true root in range. Return the bound whose
        # NPV is closest to zero (best achievable approximation).
        return lower if abs(npv_lower) < abs(npv_upper) else upper

    for _ in range(max_iterations):
        mid = (lower + upper) / 2
        npv_mid = net_present_value(mid, cashflows)
        if abs(npv_mid) < tolerance:
            return mid
        if npv_lower * npv_mid < 0:
            upper = mid
            npv_upper = npv_mid
        else:
            lower = mid
            npv_lower = npv_mid

    return (lower + upper) / 2


def elss_irr(
    gross_annual_return: float,
    tax_bracket: float,
    monthly_sip: float,
    has_80c_headroom: bool,
    years: float = ELSS_LOCK_IN_YEARS,
) -> float:
    """Effective annual return of an ELSS SIP after factoring in the 80C benefit.

    ELSS has a 3-year lock-in and a one-time Section 80C deduction benefit.
    Modelling the entry benefit as a simple rate adjustment overstates it,
    so we model the actual cash flows and solve for the IRR:

    * monthly SIP outflows,
    * annual tax refunds from the 80C deduction (if headroom remains),
    * a terminal redemption value net of 10% long-term capital gains tax.

    Returns the equivalent *after-tax* annualised return as a float
    (e.g. ``0.1523`` for 15.23%).
    """
    months = int(round(years * 12))
    monthly_rate = (1 + gross_annual_return) ** (1 / 12) - 1

    # Future value of a monthly SIP invested at the end of each month.
    if monthly_rate != 0:
        future_value = monthly_sip * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
    else:
        future_value = monthly_sip * months

    principal = monthly_sip * months
    taxable_gain = max(0.0, future_value - principal)
    capital_gains_tax = taxable_gain * EQUITY_LTCG_RATE
    terminal_value = future_value - capital_gains_tax

    # Annual tax saved thanks to the Section 80C deduction.
    annual_tax_saved = monthly_sip * 12 * tax_bracket if has_80c_headroom else 0.0

    cashflows: List[float] = [-monthly_sip] * months
    for year in range(1, months // 12 + 1):
        cashflows[year * 12 - 1] += annual_tax_saved
    cashflows[-1] += terminal_value

    monthly_irr = internal_rate_of_return(cashflows)
    return (1 + monthly_irr) ** 12 - 1

