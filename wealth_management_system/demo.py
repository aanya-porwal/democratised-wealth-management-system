"""runnable demo — walks every public API and prints readable output.

this is a *demonstration* module, not the test suite. it exercises the
engines end-to-end with the sample users so anyone can see the system
working. real assertions live in ``wealth_management_system/tests/``.

run it directly::

    python -m wealth_management_system.demo
"""

import pandas as pd

from wealth_management_system.assets import ASSET_PROFILES
from wealth_management_system.models import AssetCategory, AssetClass
from wealth_management_system.planner import build_plan
from wealth_management_system.recommendation_engine import (
    best_instruments_for_need,
    get_tax_optimised_alternatives,
)
from wealth_management_system.risk_engine import assess_risk
from wealth_management_system.sample_users import meena, ravi
from wealth_management_system.utils import ensure_utf8_console

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)
pd.set_option("display.max_colwidth", 30)


def _print_goal_sanity(user) -> None:
    """print the user's derived financial properties."""
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


def _print_risk_assessment(user) -> None:
    """assess risk for a user and print a readable summary."""
    result = assess_risk(user)
    print(f"=== Risk Assessment: {user.name} ===")
    print(f"Capacity Score:  {result.capacity_score:.2f} / 1.0")
    print(f"Tolerance Score: {result.tolerance_score:.2f} / 1.0")
    print(f"Final Score:     {result.final_score_100} / 100")
    print(f"Risk Category:   {result.risk_category}")
    print(f"Capacity binding: {result.capacity_was_binding}")
    print(f"\nBreakdown: {result.breakdown}")


def _print_asset_universe() -> None:
    """verify every AssetClass has a profile and print the universe summary."""
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
    """show best debt options for two different tax brackets."""
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
    """show cross-category recommendations for several scenarios."""
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


def _print_plan(user) -> None:
    """print the full explained financial plan for a user."""
    plan = build_plan(user)
    print(f"\n=== Financial Plan: {plan.user_name} ===")
    print(plan.summary)
    print("\nActions:")
    for a in plan.actions:
        print(f"  [{a.priority}] {a.action}")
        print(f"        ↳ {a.reason}")


def _print_diagnostics() -> None:
    """explain why arbitrage isn't in the debt list and verify ELSS logic."""
    arb = ASSET_PROFILES[AssetClass.ARBITRAGE_FUND]
    print("Arbitrage fund diagnostic:")
    print(f"  category: {arb.category}")
    print(f"  min_horizon: {arb.min_horizon_years}")
    print(f"  max_horizon: {arb.max_horizon_years}")
    print(f"  min_investment: {arb.min_investment}")
    print(f"  tax_treatment: {arb.tax_treatment}")

    from wealth_management_system.recommendation_engine import NEED_CATEGORIES

    print(
        f"\n  AssetCategory.HYBRID in debt categories: "
        f"{AssetCategory.HYBRID in NEED_CATEGORIES['debt']}"
    )

    from wealth_management_system.assets import effective_return_after_tax

    eff = effective_return_after_tax(arb, tax_bracket=0.30, holding_years=3.0)
    print(f"\n  Effective return 30% bracket, 3yr: {eff:.2%}")

    from wealth_management_system.assets import elss_effective_return

    elss = ASSET_PROFILES[AssetClass.EQUITY_ELSS]
    print("\nELSS diagnostic:")
    print(f"  category: {elss.category}")
    eff_elss = elss_effective_return(
        elss, tax_bracket=0.30, monthly_investment=150000, has_80c_headroom=True
    )
    print(f"  Effective return 30% bracket, 80C headroom, 1.5L/yr: {eff_elss:.2%}")


def main() -> None:
    """run the full demo end to end."""
    ensure_utf8_console()

    print("#" * 70)
    print("RAVI — 28, SOFTWARE ENGINEER, MUMBAI")
    print("#" * 70)
    _print_goal_sanity(ravi)
    print()
    _print_risk_assessment(ravi)
    _print_plan(ravi)

    print("\n" + "#" * 70)
    print("MEENA — 44, TIER 3 CITY, SMALL BUSINESS OWNER")
    print("#" * 70)
    _print_risk_assessment(meena)
    _print_plan(meena)

    print("\n" + "#" * 70)
    print("ASSET UNIVERSE")
    print("#" * 70)
    _print_asset_universe()

    print("\n" + "#" * 70)
    print("TAX-OPTIMISED ALTERNATIVES (WITHIN CATEGORY)")
    print("#" * 70)
    _print_tax_alternatives()

    print("\n" + "#" * 70)
    print("CROSS-CATEGORY RECOMMENDATIONS")
    print("#" * 70)
    _print_recommendations()

    print("\n" + "#" * 70)
    print("DIAGNOSTICS")
    print("#" * 70)
    _print_diagnostics()


if __name__ == "__main__":
    main()

