"""Recommendation engine — tax-aware instrument selection.

Contains everything related to *recommendations*:

* ``get_tax_optimised_alternatives`` — rank instruments inside one
  category by after-tax return.
* ``best_instruments_for_need`` — the core cross-category, tax-aware
  recommendation function that maps a generic need ("safe", "debt",
  "growth", ...) to concrete instruments.

The engine only ever *reads* the ``ASSET_PROFILES`` database; it never
mutates it.
"""

from typing import Dict, List, Tuple

import pandas as pd

from wealth_management_system.assets import (
    ASSET_PROFILES,
    effective_return_after_tax,
    elss_effective_return,
)
from wealth_management_system.models import (
    AssetCategory,
    AssetClass,
    AssetClassProfile,
)

# Categories that are relevant for each generic "need" a user may express.
NEED_CATEGORIES: Dict[str, List[AssetCategory]] = {
    "safe": [
        AssetCategory.CASH_AND_LIQUID,
        AssetCategory.DEBT,
        AssetCategory.TAX_ADVANTAGED,
    ],
    "debt": [
        AssetCategory.DEBT,
        AssetCategory.HYBRID,
        AssetCategory.TAX_ADVANTAGED,
    ],
    "growth": [
        AssetCategory.EQUITY,
        AssetCategory.HYBRID,
        AssetCategory.TAX_ADVANTAGED,
    ],
    "gold": [AssetCategory.GOLD_AND_COMMODITIES],
    "real_assets": [AssetCategory.REAL_ASSETS],
    "all": list(AssetCategory),
}


def _after_tax_return(
    profile: AssetClassProfile,
    tax_bracket: float,
    years: float,
    has_80c_headroom: bool,
    monthly_investment: float = 0.0,
) -> float:
    """After-tax return for a profile, handling the ELSS special case."""
    if profile.asset_class == AssetClass.EQUITY_ELSS:
        return elss_effective_return(
            profile,
            tax_bracket=tax_bracket,
            monthly_investment=monthly_investment,
            has_80c_headroom=has_80c_headroom,
        )
    return effective_return_after_tax(
        profile, tax_bracket=tax_bracket, holding_years=years
    )


def get_tax_optimised_alternatives(
    asset_class: AssetClass,
    tax_bracket: float,
    has_80c_headroom: bool,
    has_nps_headroom: bool,
    years: float,
) -> List[Tuple[AssetClass, float, str]]:
    """Rank alternatives in the same category by after-tax return.

    Given a generic need (e.g. *"I need debt exposure for 3 years"*),
    return every compatible instrument in the same category sorted by
    after-tax return for the user's specific tax situation.

    Returns
    -------
    List[Tuple[AssetClass, float, str]]
        ``(asset_class, effective_return, reason)`` tuples, highest
        return first.

    Notes
    -----
    ``has_nps_headroom`` is accepted for API compatibility with the
    original notebook but does not currently change the ranking.
    """
    profile = ASSET_PROFILES[asset_class]
    category = profile.category

    # All asset classes in the same category with a compatible horizon.
    candidates = [
        ac
        for ac, p in ASSET_PROFILES.items()
        if p.category == category
        and p.min_horizon_years <= years
        and (p.max_horizon_years is None or p.max_horizon_years >= years)
    ]

    results: List[Tuple[AssetClass, float, str]] = []
    for ac in candidates:
        p = ASSET_PROFILES[ac]
        if ac == AssetClass.EQUITY_ELSS:
            eff = elss_effective_return(
                p,
                tax_bracket=tax_bracket,
                monthly_investment=150_000,
                has_80c_headroom=has_80c_headroom,
            )
            reason = "80C benefit included" if has_80c_headroom else "No 80C headroom"
        else:
            eff = effective_return_after_tax(
                p, tax_bracket=tax_bracket, holding_years=years
            )
            reason = p.tax_treatment.value

        results.append((ac, round(eff, 4), reason))

    return sorted(results, key=lambda item: -item[1])


def best_instruments_for_need(
    need: str,
    tax_bracket: float,
    has_80c_headroom: bool,
    has_nps_headroom: bool,
    years: float,
    monthly_investment: float,
    max_risk_level: int = 10,
    top_n: int = 8,
) -> pd.DataFrame:
    """Find the best instruments for a generic need across all categories.

    This is the core of tax-aware recommendation: given a need and the
    user's tax situation, it scans the *entire* asset universe (not just
    one category) and returns the top ``top_n`` instruments ranked by
    effective after-tax return.

    Parameters
    ----------
    need:
        One of ``"safe"``, ``"debt"``, ``"growth"``, ``"gold"``,
        ``"real_assets"`` or ``"all"``.
    tax_bracket:
        User's marginal tax rate as a fraction.
    has_80c_headroom:
        Whether the user still has Section 80C deduction capacity.
    has_nps_headroom:
        Whether the user still has NPS 80CCD(1B) capacity.
    years:
        Investment horizon in years.
    monthly_investment:
        Planned monthly investment amount in rupees.
    max_risk_level:
        Highest acceptable risk level (1–10).
    top_n:
        Number of instruments to return.

    Returns
    -------
    pd.DataFrame
        Sorted, formatted table of the best instruments.
    """
    relevant_categories = NEED_CATEGORIES.get(need, list(AssetCategory))

    results = []
    for ac, p in ASSET_PROFILES.items():
        # Skip if wrong category
        if p.category not in relevant_categories:
            continue
        # Skip if horizon incompatible
        if p.min_horizon_years > years:
            continue
        if p.max_horizon_years is not None and p.max_horizon_years < years:
            continue
        # Skip if minimum investment too high for monthly amount
        if p.min_investment > monthly_investment * 3:
            continue
        # Skip if too risky for this need
        if p.risk_level > max_risk_level:
            continue

        # Calculate effective (after-tax) return
        eff = _after_tax_return(
            p,
            tax_bracket=tax_bracket,
            years=years,
            has_80c_headroom=has_80c_headroom,
            monthly_investment=monthly_investment,
        )

        # What ₹1L grows to after-tax over the horizon
        projected = 100_000 * (1 + eff) ** years

        results.append(
            {
                "instrument": ac.value,
                "category": p.category.value,
                "gross_return": p.expected_annual_return,
                "effective_return": eff,
                "projected_1L": round(projected),
                "risk_level": p.risk_level,
                "lock_in_yrs": p.lock_in_years,
                "tax_treatment": p.tax_treatment.value,
                "deduction": p.deduction_benefit.value,
                "liquidity": p.liquidity_score,
            }
        )

    df = pd.DataFrame(results)
    df = df.sort_values("effective_return", ascending=False).head(top_n)
    df["gross_return"] = df["gross_return"].map("{:.2%}".format)
    df["effective_return"] = df["effective_return"].map("{:.2%}".format)
    df["projected_1L"] = df["projected_1L"].map("₹{:,.0f}".format)

    return df.reset_index(drop=True)

