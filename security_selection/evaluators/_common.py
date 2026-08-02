"""Shared helpers and mixins for all evaluators.

This module eliminates duplication across the 14+ evaluator classes by
providing:

* :class:`EvaluatorMixin` — default implementations of stages that are
  identical across asset classes (validate, fetch common patterns).
* :func:`build_candidates_from_payloads` — convert a list of provider
  payloads into ``CandidateSecurity`` objects.
* :func:`default_benchmark_symbol` — map an asset class to a sensible
  default benchmark.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from security_selection.base.provider import BaseProviderSet
from security_selection.config import SecuritySelectionConfig
from security_selection.metrics.engine import MetricsEngine
from security_selection.models.data import (
    HistoricalSeries,
    MarketSnapshot,
    ProviderPayload,
    SecurityIdentity,
)
from security_selection.models.enums import (
    AssetClassBucket,
    SecurityKind,
    TargetAssetClass,
)
from security_selection.models.pipeline import CandidateSecurity
from security_selection.quality.engine import DataQualityEngine

logger = logging.getLogger(__name__)

# ── default benchmark symbols per asset class ────────────────────────

DEFAULT_BENCHMARKS: Dict[str, str] = {
    "large_cap_equity": "^NSEI",           # Nifty 50
    "mid_cap_equity": "^NSEMDCP50",        # Nifty Midcap 50
    "small_cap_equity": "^NSESCP50",       # Nifty Smallcap 50
    "flexi_cap_equity": "^NSEI",           # Nifty 50 as proxy
    "elss_equity": "^NSEI",                # ELSS benchmark ~ Nifty 50
    "international_equity": "^GSPC",       # S&P 500 (via yfinance ^GSPC)
    "debt": "^NSEBANK",                    # Nifty Bank as debt proxy (or use Nifty 10yr G-sec)
    "corporate_bonds": "NSEGOVT10YR",      # 10yr G-sec as corporate bond proxy
    "government_bonds": "NSEGOVT10YR",
    "gold": "GC=F",                        # Gold futures (COMEX)
    "gold_etf": "GC=F",
    "sgb": "GC=F",
    "reit": "^NSEI",
    "invit": "^NSEI",
    "fixed_deposit": None,
    "ppf": None,
    "nps": None,
    "stocks": "^NSEI",
}

# ── currency per asset class ─────────────────────────────────────────

DEFAULT_CURRENCIES: Dict[str, str] = {
    "large_cap_equity": "INR",
    "mid_cap_equity": "INR",
    "small_cap_equity": "INR",
    "flexi_cap_equity": "INR",
    "elss_equity": "INR",
    "international_equity": "USD",
    "debt": "INR",
    "corporate_bonds": "INR",
    "government_bonds": "INR",
    "gold": "INR",
    "gold_etf": "INR",
    "sgb": "INR",
    "reit": "INR",
    "invit": "INR",
    "fixed_deposit": "INR",
    "ppf": "INR",
    "nps": "INR",
    "stocks": "INR",
}

# ── bucket mapping per asset class ───────────────────────────────────

BUCKET_MAP: Dict[str, AssetClassBucket] = {
    "large_cap_equity": AssetClassBucket.EQUITY,
    "mid_cap_equity": AssetClassBucket.EQUITY,
    "small_cap_equity": AssetClassBucket.EQUITY,
    "flexi_cap_equity": AssetClassBucket.EQUITY,
    "elss_equity": AssetClassBucket.EQUITY,
    "international_equity": AssetClassBucket.INTERNATIONAL_EQUITY,
    "debt": AssetClassBucket.DEBT,
    "corporate_bonds": AssetClassBucket.DEBT,
    "government_bonds": AssetClassBucket.DEBT,
    "gold": AssetClassBucket.GOLD,
    "gold_etf": AssetClassBucket.GOLD,
    "sgb": AssetClassBucket.GOLD,
    "reit": AssetClassBucket.REAL_ASSETS,
    "invit": AssetClassBucket.REAL_ASSETS,
    "fixed_deposit": AssetClassBucket.FIXED_DEPOSITS,
    "ppf": AssetClassBucket.TAX_ADVANTAGED,
    "nps": AssetClassBucket.TAX_ADVANTAGED,
    "stocks": AssetClassBucket.EQUITY,
}

# ── security kind per asset class ────────────────────────────────────

KIND_MAP: Dict[str, SecurityKind] = {
    "large_cap_equity": SecurityKind.ETF,
    "mid_cap_equity": SecurityKind.ETF,
    "small_cap_equity": SecurityKind.ETF,
    "flexi_cap_equity": SecurityKind.ETF,
    "elss_equity": SecurityKind.MUTUAL_FUND,
    "international_equity": SecurityKind.INTERNATIONAL_FUND,
    "debt": SecurityKind.CORPORATE_BOND,
    "corporate_bonds": SecurityKind.CORPORATE_BOND,
    "government_bonds": SecurityKind.GOVERNMENT_BOND,
    "gold": SecurityKind.GOLD_ETF,
    "gold_etf": SecurityKind.GOLD_ETF,
    "sgb": SecurityKind.SGB,
    "reit": SecurityKind.REIT,
    "invit": SecurityKind.INVIT,
    "fixed_deposit": SecurityKind.FIXED_DEPOSIT,
    "ppf": SecurityKind.PPF,
    "nps": SecurityKind.NPS,
    "stocks": SecurityKind.STOCK,
}


def default_benchmark_symbol(target: TargetAssetClass) -> str | None:
    """Return the default benchmark symbol for the given asset class."""
    return DEFAULT_BENCHMARKS.get(target.value)


def default_currency(target: TargetAssetClass) -> str:
    """Return the default currency for the given asset class."""
    return DEFAULT_CURRENCIES.get(target.value, "INR")


def bucket_for(target: TargetAssetClass) -> AssetClassBucket:
    """Return the allocation bucket for the given asset class."""
    return BUCKET_MAP.get(target.value, AssetClassBucket.EQUITY)


def kind_for(target: TargetAssetClass) -> SecurityKind:
    """Return the security kind for the given asset class."""
    return KIND_MAP.get(target.value, SecurityKind.ETF)


def build_candidates_from_payloads(
    payloads: List[ProviderPayload],
    target: TargetAssetClass,
    *,
    bucket: AssetClassBucket | None = None,
    kind: SecurityKind | None = None,
) -> List[CandidateSecurity]:
    """Convert provider payloads into ``CandidateSecurity`` objects.

    Parameters
    ----------
    payloads:
        The validated provider payloads.
    target:
        The target asset class for the candidates.
    bucket:
        Override the default bucket. Falls back to ``bucket_for(target)``.
    kind:
        Override the default kind. Falls back to ``kind_for(target)``.

    Returns
    -------
    List[CandidateSecurity]
        Candidate security objects, one per successful payload.
    """
    bucket_val = bucket or bucket_for(target)
    kind_val = kind or kind_for(target)
    candidates: List[CandidateSecurity] = []
    for payload in payloads:
        if not payload.success:
            continue
        candidate = CandidateSecurity(
            identity=payload.identity,
            kind=kind_val,
            asset_class=target,
            bucket=bucket_val,
            snapshot=payload.snapshot,
            history=payload.history,
            metrics=dict(payload.metrics or {}),
            data_sources=[payload.provider.value],
        )
        # Populate holdings/sector/country from payload if available
        if payload.holdings:
            candidate.holdings = payload.holdings
        if payload.sector_allocations:
            candidate.sector_allocations = payload.sector_allocations
        if payload.metrics and "sector_allocations" in payload.metrics:
            candidate.sector_allocations = {
                k: float(v)
                for k, v in payload.metrics.get("sector_allocations", {}).items()
            }
        if payload.metrics and "country_allocations" in payload.metrics:
            candidate.country_allocations = {
                k: float(v)
                for k, v in payload.metrics.get("country_allocations", {}).items()
            }
        candidates.append(candidate)
    return candidates


def enrich_candidate_from_metrics(
    candidate: CandidateSecurity,
    metrics_engine: MetricsEngine,
    config: SecuritySelectionConfig,
) -> None:
    """Compute and attach all available metrics to a candidate.

    This is a convenience wrapper that calls ``metrics_engine.compute``
    and populates the candidate's ``metrics`` and ``unavailable`` dicts.

    Parameters
    ----------
    candidate:
        The candidate to enrich (mutated in place).
    metrics_engine:
        The metrics engine instance.
    config:
        The security selection config (for benchmark lookup).
    """
    benchmark_symbol = default_benchmark_symbol(candidate.asset_class)
    result = metrics_engine.compute(
        candidate=candidate,
        benchmark_symbol=benchmark_symbol,
        risk_free_rate=config.optimization.risk_free_rate,
    )
    # Merge computed metrics into candidate.metrics
    for key, value in result.computed.items():
        if value is not None:
            candidate.metrics[key] = value
        else:
            candidate.unavailable[key] = result.unavailable.get(
                key, "could not be derived"
            )
    # Attach benchmark if computed
    if result.benchmark_series is not None:
        candidate.meta["benchmark_series"] = result.benchmark_series
