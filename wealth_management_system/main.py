"""Orchestration entry point for the wealth management system.

Kept intentionally thin — imports the public API from the domain
modules and prints a readable summary. All business logic lives in the
engine modules (``risk_engine``, ``assets``, ``recommendation_engine``),
and all sample data lives in ``tests``.
"""

import pandas as pd

from wealth_management_system.recommendation_engine import (
    best_instruments_for_need,
)
from wealth_management_system.risk_engine import assess_risk
from wealth_management_system.sample_users import ravi
from wealth_management_system.utils import ensure_utf8_console

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)
pd.set_option("display.max_colwidth", 30)


def _print_risk(profile) -> None:
    """Assess and print the risk summary for a user."""
    risk = assess_risk(profile)
    print(f"=== Risk Assessment: {profile.name} ===")
    print(f"Capacity Score:  {risk.capacity_score:.2f} / 1.0")
    print(f"Tolerance Score: {risk.tolerance_score:.2f} / 1.0")
    print(f"Final Score:     {risk.final_score_100} / 100")
    print(f"Risk Category:   {risk.risk_category}")
    print(f"Capacity binding: {risk.capacity_was_binding}")


def _print_recommendations(profile) -> None:
    """Print the top investment recommendations for a user."""
    tax_bracket = profile.financial.tax_bracket_percent / 100
    columns = [
        "instrument",
        "category",
        "gross_return",
        "effective_return",
        "projected_1L",
        "risk_level",
        "lock_in_yrs",
        "deduction",
    ]
    recommendations = best_instruments_for_need(
        need="growth",
        tax_bracket=tax_bracket,
        has_80c_headroom=True,
        has_nps_headroom=True,
        years=7,
        monthly_investment=10000,
    )
    print(f"\n=== Recommendations: {profile.name} ===")
    print(recommendations[columns].to_string(index=False))


def main() -> None:
    """Run the end-to-end demo: risk assessment + recommendations."""
    ensure_utf8_console()
    _print_risk(ravi)
    _print_recommendations(ravi)


if __name__ == "__main__":
    main()

