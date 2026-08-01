"""Demo/test users and runnable sanity checks.

This module defines the two sample users (``ravi`` and ``meena``) used
throughout the project. Importing this module has no side effects; all
prints happen only when the module is executed directly::

    python tests.py

The module also demonstrates every public API:

* risk assessment (``risk_engine.assess_risk``)
* asset-universe verification (``assets.ASSET_PROFILES``)
* tax-optimised alternatives (``recommendation_engine.get_tax_optimised_alternatives``)
* cross-category recommendations (``recommendation_engine.best_instruments_for_need``)
"""

from datetime import date

import pandas as pd

from wealth_management_system.assets import ASSET_PROFILES
from wealth_management_system.models import (
    AssetCategory,
    AssetClass,
    BehavioralProfile,
    EmploymentType,
    FinancialProfile,
    Goal,
    GoalPriority,
    GoalType,
    RiskToleranceLevel,
    UserProfile,
)
from wealth_management_system.recommendation_engine import (
    best_instruments_for_need,
    get_tax_optimised_alternatives,
)
from wealth_management_system.risk_engine import assess_risk
from wealth_management_system.sample_users import meena, ravi
from wealth_management_system.utils import ensure_utf8_console


# ─────────────────────────────────────────────────────────────────────
# Demo / sanity-check prints (only when run directly)
# ─────────────────────────────────────────────────────────────────────


def _print_goal_sanity(user: UserProfile) -> None:
    """Print the user's derived financial properties."""
    print(f"Monthly surplus: ₹{user.financial.monthly_surplus():,.0f}")
    print(f"Investable surplus: ₹{user.investable_surplus():,.0f}")
    print(f"Debt-to-income: {user.financial.debt_to_income_ratio():.1%}")
    print(f"Net worth: ₹{user.financial.net_worth():,.0f}")
    print(f"Life stage: {user.life_stage()}")
    print(f"Years to retirement: {user.years_to_retirement():.0f}")

    for goal in user.goals:
        print(f"\nGoal: {goal.goal_type.value}")
        print(f"  Years remaining: {goal.years_to_goal():.1f}")
        print(f"  Amount remaining: ₹{goal.amount_remaining():,.0f}")


def _print_risk_assessment(user: UserProfile) -> None:
    """Assess risk for a user and print a readable summary."""
    result = assess_risk(user)
    print(f"=== Risk Assessment: {user.name} ===")
    print(f"Capacity Score:  {result.capacity_score:.2f} / 1.0")
    print(f"Tolerance Score: {result.tolerance_score:.2f} / 1.0")
    print(f"Final Score:     {result.final_score_100} / 100")
    print(f"Risk Category:   {result.risk_category}")
    print(f"Capacity binding: {result.capacity_was_binding}")
    print(f"\nBreakdown: {result.breakdown}")


def _print_asset_universe() -> None:
    """Verify every AssetClass has a profile and print the universe summary."""
    defined = set(ASSET_PROFILES.keys())
    missing = set(AssetClass) - defined

    if missing:
        print(f"⚠️  Missing profiles for: {missing}")
    else:
        print(f"✅  All {len(defined)} asset classes have profiles")

    df = pd.DataFrame(
        [
            {
                "asset": ac.value,
                "category": ASSET_PROFILES[ac].category.value,
                "return": f"{ASSET_PROFILES[ac].expected_annual_return:.1%}",
                "volatility": f"{ASSET_PROFILES[ac].annual_volatility:.1%}",
                "risk_level": ASSET_PROFILES[ac].risk_level,
                "lock_in": ASSET_PROFILES[ac].lock_in_years,
                "tax": ASSET_PROFILES[ac].tax_treatment.value,
                "deduction": ASSET_PROFILES[ac].deduction_benefit.value,
                "min_invest": f"₹{ASSET_PROFILES[ac].min_investment:,.0f}",
            }
            for ac in AssetClass
        ]
    )
    print(f"\nFull asset universe ({len(df)} instruments):\n")
    print(df.to_string(index=False))


def _print_tax_alternatives() -> None:
    """Show best debt options for two different tax brackets."""
    print("Best debt options for 30% bracket, 3yr horizon:")
    print("─" * 60)
    for ac, ret, reason in get_tax_optimised_alternatives(
        AssetClass.SHORT_DURATION_FUND,
        tax_bracket=0.30,
        has_80c_headroom=True,
        has_nps_headroom=True,
        years=3,
    ):
        print(f"  {ac.value:<30} {ret:.2%}  ({reason})")

    print("\nSame for 5% bracket user:")
    print("─" * 60)
    for ac, ret, reason in get_tax_optimised_alternatives(
        AssetClass.SHORT_DURATION_FUND,
        tax_bracket=0.05,
        has_80c_headroom=True,
        has_nps_headroom=True,
        years=3,
    ):
        print(f"  {ac.value:<30} {ret:.2%}  ({reason})")


def _print_recommendations() -> None:
    """Show cross-category recommendations for several scenarios."""
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    pd.set_option("display.max_colwidth", 30)

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

    print("=" * 80)
    print("SAFE/DEBT INSTRUMENTS — 30% BRACKET, 3 YEAR HORIZON")
    print("(hasn't used 80C limit yet)")
    print("=" * 80)
    df_30 = best_instruments_for_need(
        need="debt",
        tax_bracket=0.30,
        has_80c_headroom=True,
        has_nps_headroom=True,
        years=3,
        monthly_investment=10000,
    )
    print(df_30[columns].to_string())

    print("\n")
    print("=" * 80)
    print("SAME NEED — 5% BRACKET, 3 YEAR HORIZON")
    print("=" * 80)
    df_5 = best_instruments_for_need(
        need="debt",
        tax_bracket=0.05,
        has_80c_headroom=True,
        has_nps_headroom=True,
        years=3,
        monthly_investment=10000,
    )
    print(df_5[columns].to_string())

    print("\n")
    print("=" * 80)
    print("GROWTH INSTRUMENTS — 30% BRACKET, 7 YEAR HORIZON")
    print("80C headroom available")
    print("=" * 80)
    df_growth = best_instruments_for_need(
        need="growth",
        tax_bracket=0.30,
        has_80c_headroom=True,
        has_nps_headroom=True,
        years=7,
        monthly_investment=10000,
    )
    print(df_growth[columns].to_string())


def _print_diagnostics() -> None:
    """Explain why arbitrage isn't in the debt list and verify ELSS logic."""
    arb = ASSET_PROFILES[AssetClass.ARBITRAGE_FUND]
    print("Arbitrage fund diagnostic:")
    print(f"  category: {arb.category}")
    print(f"  min_horizon: {arb.min_horizon_years}")
    print(f"  max_horizon: {arb.max_horizon_years}")
    print(f"  min_investment: {arb.min_investment}")
    print(f"  tax_treatment: {arb.tax_treatment}")

    # Is it in the 'debt' need categories?
    from wealth_management_system.recommendation_engine import NEED_CATEGORIES

    print(
        f"\n  AssetCategory.HYBRID in debt categories: "
        f"{AssetCategory.HYBRID in NEED_CATEGORIES['debt']}"
    )

    # What's its effective return for 30% bracket, 3yr?
    from wealth_management_system.assets import effective_return_after_tax

    eff = effective_return_after_tax(arb, tax_bracket=0.30, holding_years=3.0)
    print(f"\n  Effective return 30% bracket, 3yr: {eff:.2%}")

    # Diagnose ELSS
    from wealth_management_system.assets import elss_effective_return

    elss = ASSET_PROFILES[AssetClass.EQUITY_ELSS]
    print("\nELSS diagnostic:")
    print(f"  category: {elss.category}")
    eff_elss = elss_effective_return(elss, tax_bracket=0.30, monthly_investment=150000, has_80c_headroom=True)
    print(f"  Effective return 30% bracket, 80C headroom, 1.5L/yr: {eff_elss:.2%}")


if __name__ == "__main__":
    ensure_utf8_console()
    # 1. Ravi — 28, software engineer, Mumbai
    print("#" * 70)
    print("RAVI — 28, SOFTWARE ENGINEER, MUMBAI")
    print("#" * 70)
    _print_goal_sanity(ravi)
    print()
    _print_risk_assessment(ravi)

    # 2. Meena — 44, tier 3 city, small business owner
    print("\n" + "#" * 70)
    print("MEENA — 44, TIER 3 CITY, SMALL BUSINESS OWNER")
    print("#" * 70)
    _print_risk_assessment(meena)

    # 3. Asset universe verification
    print("\n" + "#" * 70)
    print("ASSET UNIVERSE")
    print("#" * 70)
    _print_asset_universe()

    # 4. Tax-optimised alternatives within one category
    print("\n" + "#" * 70)
    print("TAX-OPTIMISED ALTERNATIVES (WITHIN CATEGORY)")
    print("#" * 70)
    _print_tax_alternatives()

    # 5. Cross-category recommendations
    print("\n" + "#" * 70)
    print("CROSS-CATEGORY RECOMMENDATIONS")
    print("#" * 70)
    _print_recommendations()

    # 6. Diagnostics
    print("\n" + "#" * 70)
    print("DIAGNOSTICS")
    print("#" * 70)
    _print_diagnostics()

