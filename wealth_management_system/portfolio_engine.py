"""portfolio engine — risk capacity to a real target allocation.

this engine answers the planner's step seven: given how much risk the
user can actually take, what should their money look like?

it produces:

* a strategic asset allocation (equity / debt / gold / cash) derived
  from the risk assessment
* a concrete instrument list for each bucket, tax-aware, reusing the
  asset database (``best_instruments_for_need``)

the allocation is *strategic* — it is a long-term target, not a market
call. no timing, no sector bets.
"""

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from wealth_management_system.assets import ASSET_PROFILES
from wealth_management_system.models import (
    AssetCategory,
    AssetClass,
    UserProfile,
)
from wealth_management_system.recommendation_engine import (
    best_instruments_for_need,
)
from wealth_management_system.risk_engine import assess_risk

# strategic equity weight by risk score (0-100).
# these are conservative glidepath anchors. a 70 risk score does not get
# a 100% equity portfolio — nobody should be 100% equity.
EQUITY_WEIGHT_BY_SCORE: List[tuple] = [
    (20, 0.10),   # very conservative
    (35, 0.25),
    (50, 0.40),
    (65, 0.55),
    (80, 0.65),
    (100, 0.75),  # even maxed-out risk never goes above 75% equity
]

# residual split for the non-equity portion
DEBT_DEFAULT_SHARE: float = 0.80
GOLD_SHARE: float = 0.10
CASH_SHARE: float = 0.10


@dataclass
class PortfolioSlice:
    """one strategic bucket and its concrete instruments."""

    bucket: str  # equity / debt / gold / cash
    weight: float  # 0.0 to 1.0 of the investable amount
    instruments: List[AssetClass] = field(default_factory=list)


@dataclass
class PortfolioPlan:
    """the complete strategic allocation for a user."""

    risk_score: int
    risk_category: str
    slices: List[PortfolioSlice] = field(default_factory=list)

    def bucket_weight(self, bucket: str) -> float:
        """weight of one bucket (0.0-1.0)."""
        for s in self.slices:
            if s.bucket == bucket:
                return s.weight
        return 0.0


def _equity_weight(risk_score: int) -> float:
    """interpolate the equity weight from the glidepath anchors."""
    risk_score = min(max(risk_score, 0), 100)
    for threshold, weight in EQUITY_WEIGHT_BY_SCORE:
        if risk_score <= threshold:
            return weight
    return EQUITY_WEIGHT_BY_SCORE[-1][1]


def build_portfolio(
    user: UserProfile,
    years: float = 7.0,
    monthly_investment: float = 0.0,
    top_instruments: int = 3,
) -> PortfolioPlan:
    """build the strategic allocation and instrument list for a user."""
    risk = assess_risk(user)
    equity = _equity_weight(risk.final_score_100)

    # non-equity split: debt gets most, gold and cash small stabilisers
    non_equity = 1.0 - equity
    debt = non_equity * DEBT_DEFAULT_SHARE
    gold = non_equity * GOLD_SHARE
    cash = non_equity * CASH_SHARE

    tax_bracket = user.financial.tax_bracket_percent / 100
    has_80c_headroom = True
    has_nps_headroom = True
    # if no monthly amount given, use the user's investable surplus.
    # floor it so the min_investment filters don't wipe out every
    # instrument for a user with a tiny surplus.
    monthly = max(monthly_investment or max(0, user.investable_surplus()), 500)

    slices: List[PortfolioSlice] = []

    # equity bucket — long horizon, growth
    equity_df = best_instruments_for_need(
        need="growth",
        tax_bracket=tax_bracket,
        has_80c_headroom=has_80c_headroom,
        has_nps_headroom=has_nps_headroom,
        years=years,
        monthly_investment=monthly,
        max_risk_level=8,
        top_n=top_instruments,
    )
    slices.append(
        PortfolioSlice(
            bucket="equity",
            weight=round(equity, 3),
            instruments=[_ac_from_row(r) for r in equity_df.itertuples()],
        )
    )

    # debt bucket — stability and shorter horizons
    debt_df = best_instruments_for_need(
        need="debt",
        tax_bracket=tax_bracket,
        has_80c_headroom=has_80c_headroom,
        has_nps_headroom=has_nps_headroom,
        years=max(years, 3),
        monthly_investment=monthly,
        max_risk_level=4,
        top_n=top_instruments,
    )
    slices.append(
        PortfolioSlice(
            bucket="debt",
            weight=round(debt, 3),
            instruments=[_ac_from_row(r) for r in debt_df.itertuples()],
        )
    )

    # gold bucket — small diversifier, insurance against tail risk
    gold_df = best_instruments_for_need(
        need="gold",
        tax_bracket=tax_bracket,
        has_80c_headroom=has_80c_headroom,
        has_nps_headroom=has_nps_headroom,
        years=max(years, 5),
        monthly_investment=monthly,
        max_risk_level=5,
        top_n=min(top_instruments, 2),
    )
    slices.append(
        PortfolioSlice(
            bucket="gold",
            weight=round(gold, 3),
            instruments=[_ac_from_row(r) for r in gold_df.itertuples()],
        )
    )

    # cash bucket — liquidity, emergency buffer, near-term needs.
    # this comes straight from the asset database filtered to the
    # cash_and_liquid category, not the "safe" need (which mixes in debt
    # and tax-advantaged products that are not truly liquid).
    cash_candidates = [
        ac
        for ac, p in ASSET_PROFILES.items()
        if p.category == AssetCategory.CASH_AND_LIQUID
        and p.min_horizon_years <= 1.0
        and (p.max_horizon_years is None or p.max_horizon_years >= 1.0)
        and p.liquidity_score >= 0.9
    ]
    slices.append(
        PortfolioSlice(
            bucket="cash",
            weight=round(cash, 3),
            instruments=sorted(cash_candidates, key=lambda ac: -ASSET_PROFILES[ac].liquidity_score)[
                :2
            ],
        )
    )

    return PortfolioPlan(
        risk_score=risk.final_score_100,
        risk_category=risk.risk_category,
        slices=slices,
    )


def _ac_from_row(row) -> AssetClass:
    """recover the AssetClass enum from a recommendation table row."""
    return AssetClass(row.instrument)

