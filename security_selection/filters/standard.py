"""Standard configurable filters.

Each filter is its own class implementing :class:`BaseFilter`. Limits are
read from the config defaults and may be overridden per request.
"""

from __future__ import annotations

from typing import Any, Dict

from security_selection.config import FilterDefaultsConfig
from security_selection.filters.base import BaseFilter, FilterResult
from security_selection.models.pipeline import CandidateSecurity


class MinAUMFilter(BaseFilter):
    """Reject securities below the minimum AUM threshold (₹ crores)."""

    name = "min_aum"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        limit = float(self._limit(overrides, "min_aum_crore", self._defaults.min_aum_crore))
        aum = self._metric(candidate, "aum_crore")
        if aum is None:
            return FilterResult(False, "AUM not available")
        if float(aum) < limit:
            return FilterResult(False, f"AUM ₹{aum:,.2f}cr < minimum ₹{limit:,.2f}cr")
        return FilterResult(True)


class ExpenseRatioFilter(BaseFilter):
    """Reject funds with expense ratio above the cap."""

    name = "max_expense_ratio"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        cap = float(self._limit(overrides, "max_expense_ratio", self._defaults.max_expense_ratio))
        expense = self._metric(candidate, "expense_ratio")
        if expense is None:
            # Some asset classes (FD/PPF/NPS) have no expense ratio; don't reject.
            return FilterResult(True, "no expense ratio (N/A for this instrument)")
        if float(expense) > cap:
            return FilterResult(False, f"expense ratio {float(expense):.2%} > cap {cap:.2%}")
        return FilterResult(True)


class LiquidityFilter(BaseFilter):
    """Reject securities below the minimum normalized liquidity score."""

    name = "min_liquidity"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        floor = float(self._limit(overrides, "min_liquidity_score", self._defaults.min_liquidity_score))
        liquidity = self._profile(candidate, "liquidity")
        if liquidity is None:
            # fall back to the metric
            liquidity = self._metric(candidate, "liquidity_score")
        if liquidity is None:
            return FilterResult(False, "liquidity not available")
        if float(liquidity) < floor:
            return FilterResult(False, f"liquidity {float(liquidity):.2f} < floor {floor:.2f}")
        return FilterResult(True)


class AgeFilter(BaseFilter):
    """Reject instruments younger than the minimum track-record age."""

    name = "min_age"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        min_years = float(self._limit(overrides, "min_age_years", self._defaults.min_age_years))
        age = self._metric(candidate, "age_years")
        if age is None:
            return FilterResult(False, "inception age not available")
        if float(age) < min_years:
            return FilterResult(False, f"age {float(age):.1f}y < minimum {min_years:.1f}y")
        return FilterResult(True)


class CreditRatingFilter(BaseFilter):
    """Reject bonds below the minimum credit rating."""

    name = "min_credit_rating"

    # simple ordinal scale
    _ORDINAL = {
        "AAA": 0,
        "AA": 1,
        "A": 2,
        "BBB": 3,
        "BB": 4,
        "B": 5,
        "CCC": 6,
        "unrated": 7,
    }

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        minimum = str(self._limit(overrides, "min_credit_rating", self._defaults.min_credit_rating))
        rating = self._metric(candidate, "credit_rating")
        if rating is None:
            # Non-debt instruments have no credit rating; don't reject.
            return FilterResult(True, "no credit rating (N/A for this instrument)")
        rating_str = str(rating).upper()
        min_ord = self._ORDINAL.get(minimum.upper(), 1)
        got_ord = self._ORDINAL.get(rating_str, 7)
        if got_ord > min_ord:
            return FilterResult(False, f"credit rating {rating_str} below minimum {minimum}")
        return FilterResult(True)


class TrackingErrorFilter(BaseFilter):
    """Reject index funds/ETFs with excessive tracking error."""

    name = "max_tracking_error"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        cap = float(overrides.get("max_tracking_error", 0.05))
        te = self._metric(candidate, "tracking_error")
        if te is None:
            return FilterResult(True, "no tracking error (N/A)")
        if float(te) > cap:
            return FilterResult(False, f"tracking error {float(te):.2%} > cap {cap:.2%}")
        return FilterResult(True)


class RegionFilter(BaseFilter):
    """Restrict candidates to a market region."""

    name = "region"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        allowed = overrides.get("region")
        if not allowed:
            return FilterResult(True)
        region = candidate.meta.get("region")
        if region is None:
            return FilterResult(True, "region unknown — not restricted")
        if isinstance(allowed, str):
            allowed = [allowed]
        if region not in allowed:
            return FilterResult(False, f"region {region} not in allowed {allowed}")
        return FilterResult(True)


class TaxStatusFilter(BaseFilter):
    """Restrict to securities with a compatible tax status."""

    name = "tax_status"

    def check(self, candidate: CandidateSecurity, overrides: Dict[str, Any]) -> FilterResult:
        allowed = overrides.get("tax_status")
        if not allowed:
            return FilterResult(True)
        status = candidate.meta.get("tax_status")
        if status is None:
            return FilterResult(True, "tax status unknown — not restricted")
        if isinstance(allowed, str):
            allowed = [allowed]
        if status not in allowed:
            return FilterResult(False, f"tax status {status} not in allowed {allowed}")
        return FilterResult(True)


# registry of all standard filters by name
STANDARD_FILTERS = [
    MinAUMFilter,
    ExpenseRatioFilter,
    LiquidityFilter,
    AgeFilter,
    CreditRatingFilter,
    TrackingErrorFilter,
    RegionFilter,
    TaxStatusFilter,
]


def build_standard_filters(defaults: FilterDefaultsConfig) -> list[BaseFilter]:
    return [cls(defaults) for cls in STANDARD_FILTERS]

