"""Independent factor classes.

Every factor is its own class implementing :class:`BaseFactor`. A factor
takes a :class:`CandidateSecurity` and returns a 0..1 score (higher =
better) plus a short human-readable detail for explainability.

The factors:
    expected_return, risk, cost, liquidity, quality, diversification,
    tax, tracking, credit_quality, market_exposure

Each factor gracefully handles missing data: if the underlying metric is
unavailable it returns a neutral score (0.5) with an explanatory detail.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from security_selection.models.pipeline import CandidateSecurity, NormalizedProfile
from security_selection.utils.math import clamp, safe_float


class BaseFactor(ABC):
    """A single scoring factor."""

    name: str = "base"

    @abstractmethod
    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        """Return (score 0..1, details dict)."""


class ExpectedReturnFactor(BaseFactor):
    """Scores the annualized expected return of the security.

    Uses the 3y CAGR when available, else 1y, else the normalized
    expected-return axis. Higher returns score higher, capped at 25%.
    """

    name = "return_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        m = candidate.metrics
        cagr = safe_float(m.get("cagr")) or safe_float(m.get("return_3y"))
        if cagr is None:
            cagr = safe_float(m.get("return_1y"))
        if cagr is not None:
            # scale: 0% → 0, 15% → 0.75, 25%+ → 1.0
            s = clamp(cagr / 0.20)
            return s, {"cagr": round(cagr, 4)}
        if candidate.profile is not None:
            return candidate.profile.expected_return, {"using_normalized": True}
        return 0.5, {"unavailable": "no return data"}


class RiskFactor(BaseFactor):
    """Scores risk inversely: lower volatility & drawdown score higher."""

    name = "risk_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        m = candidate.metrics
        vol = safe_float(m.get("volatility"))
        mdd = safe_float(m.get("max_drawdown"))
        details: Dict[str, Any] = {}
        if vol is None:
            if candidate.profile is not None:
                s = 1.0 - candidate.profile.risk
                return s, {"using_normalized": True}
            return 0.5, {"unavailable": "no volatility data"}
        # vol 5% → ~1.0, 35% → ~0.0
        s_vol = clamp(1.0 - (vol - 0.05) / 0.30)
        details["volatility"] = round(vol, 4)
        if mdd is not None:
            s_mdd = clamp(1.0 - abs(mdd) / 0.50)
            details["max_drawdown"] = round(mdd, 4)
            s = 0.6 * s_vol + 0.4 * s_mdd
        else:
            s = s_vol
        return s, details


class CostFactor(BaseFactor):
    """Scores cost efficiency: lower expense/exit loads score higher."""

    name = "cost_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        m = candidate.metrics
        expense = safe_float(m.get("expense_ratio"))
        details: Dict[str, Any] = {}
        if expense is None:
            # asset classes without expense ratio (FD/PPF/NPS) are cost-efficient
            s = 0.9
            details["note"] = "no explicit expense ratio (assumed low-cost)"
        else:
            s = clamp(1.0 - expense / 0.03)  # 0% → 1.0, 3% → 0.0
            details["expense_ratio"] = round(expense, 4)
        exit_load = safe_float(m.get("exit_load"))
        if exit_load is not None and exit_load > 0:
            s *= (1.0 - min(exit_load, 0.03) / 0.03)
            details["exit_load"] = round(exit_load, 4)
        return s, details


class LiquidityFactor(BaseFactor):
    """Scores liquidity from the normalized profile or volume/AUM."""

    name = "liquidity_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        profile = candidate.profile
        if profile is not None and profile.liquidity > 0:
            return profile.liquidity, {"liquidity": round(profile.liquidity, 4)}
        m = candidate.metrics
        avg_vol = safe_float(m.get("average_volume"))
        if avg_vol is not None and avg_vol > 0:
            s = clamp(avg_vol / 1_000_000.0)
            return s, {"average_volume": avg_vol}
        aum = safe_float(m.get("aum_crore"))
        if aum is not None and aum > 0:
            return clamp(aum / 5000.0), {"aum_crore": aum}
        return 0.5, {"unavailable": "no liquidity data"}


class QualityFactor(BaseFactor):
    """Scores data & instrument quality (quality engine + normalized axis)."""

    name = "quality_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        details: Dict[str, Any] = {"data_quality": candidate.data_quality_score}
        profile = candidate.profile
        if profile is not None:
            s = 0.5 * candidate.data_quality_score + 0.5 * profile.quality
            return s, details
        return candidate.data_quality_score, details


class DiversificationFactor(BaseFactor):
    """Scores diversification (holdings breadth, sector spread)."""

    name = "diversification_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        profile = candidate.profile
        details: Dict[str, Any] = {}
        if profile is not None:
            return profile.diversification, {"diversification": round(profile.diversification, 4)}
        holdings = candidate.holdings
        sectors = candidate.sector_allocations
        if holdings:
            s = clamp(len(holdings) / 50.0)
            details["holdings_count"] = len(holdings)
            return s, details
        if sectors:
            s = clamp(len(sectors) / 12.0)
            details["sector_count"] = len(sectors)
            return s, details
        return 0.5, {"unavailable": "no diversification data"}


class TaxFactor(BaseFactor):
    """Scores tax efficiency from the security's tax treatment."""

    name = "tax_factor"

    _TAX_SCORES = {
        "eee": 1.0,
        "sgb_maturity": 0.95,
        "equity_ltcg": 0.85,
        "eet": 0.7,
        "reit_invit": 0.6,
        "debt_slab": 0.4,
        "none": 0.5,
    }

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        status = candidate.meta.get("tax_status")
        profile = candidate.profile
        if profile is not None and profile.tax_efficiency > 0:
            return profile.tax_efficiency, {"tax_efficiency": round(profile.tax_efficiency, 4)}
        if status is None:
            return 0.5, {"unavailable": "tax status unknown"}
        s = self._TAX_SCORES.get(status, 0.5)
        return s, {"tax_status": status}


class TrackingFactor(BaseFactor):
    """Scores tracking quality (for index funds/ETFs)."""

    name = "tracking_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        m = candidate.metrics
        te = safe_float(m.get("tracking_error"))
        details: Dict[str, Any] = {}
        if te is None:
            if candidate.profile is not None and candidate.profile.tracking_quality > 0:
                return candidate.profile.tracking_quality, {"using_normalized": True}
            return 0.7, {"note": "no tracking data; neutral for non-index instruments"}
        # TE 0% → 1.0, 5% → 0.0
        s = clamp(1.0 - te / 0.05)
        details["tracking_error"] = round(te, 4)
        return s, details


class CreditQualityFactor(BaseFactor):
    """Scores credit quality for debt securities."""

    name = "credit_quality_factor"

    _CREDIT_ORDINAL = {
        "AAA": 1.0,
        "AA": 0.9,
        "A": 0.8,
        "BBB": 0.6,
        "BB": 0.4,
        "B": 0.3,
        "CCC": 0.15,
        "unrated": 0.5,
    }

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        rating = candidate.meta.get("credit_rating")
        if rating is None:
            rating = candidate.metrics.get("credit_rating")
        if rating is None:
            # non-debt instruments: not penalized, neutral-high
            return 0.7, {"note": "no credit rating (N/A)"}
        s = self._CREDIT_ORDINAL.get(str(rating).upper(), 0.5)
        return s, {"credit_rating": str(rating)}


class MarketExposureFactor(BaseFactor):
    """Scores exposure quality: purity of exposure to the target market."""

    name = "market_exposure_factor"

    def score(self, candidate: CandidateSecurity) -> tuple[float, Dict[str, Any]]:
        profile = candidate.profile
        if profile is not None and profile.market_exposure > 0:
            return profile.market_exposure, {"using_normalized": True}
        region = candidate.meta.get("region", "india")
        # For an Indian target, Indian securities score highest.
        if region == "india":
            return 0.9, {"region": "india"}
        if region in ("us", "international", "global"):
            return 0.6, {"region": region}
        return 0.5, {"unavailable": "region unknown"}


# ── registry ─────────────────────────────────────────────────────────

FACTOR_CLASSES: list[Type[BaseFactor]] = [
    ExpectedReturnFactor,
    RiskFactor,
    CostFactor,
    LiquidityFactor,
    QualityFactor,
    DiversificationFactor,
    TaxFactor,
    TrackingFactor,
    CreditQualityFactor,
    MarketExposureFactor,
]


def build_factors() -> list[BaseFactor]:
    return [cls() for cls in FACTOR_CLASSES]

