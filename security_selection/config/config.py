"""Typed configuration loader for the Security Selection platform.

Loads ``config.yaml`` once per process and exposes the values through a
set of frozen dataclasses — mirroring the pattern used by
``wealth_management_system.config``. Every engine in the platform reads
its tunable constants from here; nothing is hardcoded.

Design notes
------------
* Dependency-light: only requires ``PyYAML`` (already a dependency).
* Nested YAML maps to nested frozen dataclasses so callers get attribute
  access and typos fail fast.
* ``get_config`` caches the loaded object per process; tests can bypass
  the cache with ``load_config``.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, TypeVar

import yaml

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config.yaml"


# ─────────────────────────────────────────────────────────────────────
# Typed configuration sections
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ScoringConfig:
    """Factor weights and score thresholds."""

    factor_weights: Mapping[str, float] = field(default_factory=dict)
    score_scale: float = 100.0
    min_recommendable_score: float = 60.0


@dataclass(frozen=True)
class RankingConfig:
    """Ranking tier sizes and confidence derivation."""

    top_n: int = 20
    top_n_10: int = 10
    top_n_5: int = 5
    alternative_count: int = 4
    completeness_weight: float = 0.5
    score_gap_weight: float = 0.5


@dataclass(frozen=True)
class OptimizationConfig:
    """Portfolio construction constraints."""

    candidate_pool_size: int = 5
    single_security_coverage_threshold: float = 0.85
    min_diversification_benefit: float = 0.05
    min_weight: float = 0.05
    max_weight: float = 0.60
    min_liquidity_score: float = 0.30
    target_portfolio_count: int = 3
    risk_free_rate: float = 0.055
    max_volatility: float = 0.30


@dataclass(frozen=True)
class FilterDefaultsConfig:
    """Default filter limits (users may override at request time)."""

    min_aum_crore: float = 100.0
    max_expense_ratio: float = 0.0125
    min_liquidity_score: float = 0.30
    min_age_years: float = 3.0
    min_credit_rating: str = "AA"
    min_avg_volume: float = 100000.0
    min_aum_ratio_floor: float = 0.001


@dataclass(frozen=True)
class ProviderSettings:
    """Common per-provider network settings."""

    enabled: bool = True
    base_url: Optional[str] = None
    timeout_seconds: Optional[float] = None
    retries: Optional[int] = None
    max_history_years: Optional[int] = None


@dataclass(frozen=True)
class ProviderConfig:
    """Provider chain and per-provider settings."""

    order: Tuple[str, ...] = ("yfinance", "mfapi", "rbi", "static")
    timeout_seconds: float = 15.0
    retries: int = 2
    yfinance: ProviderSettings = field(default_factory=ProviderSettings)
    mfapi: ProviderSettings = field(default_factory=ProviderSettings)
    rbi: ProviderSettings = field(default_factory=ProviderSettings)
    static: ProviderSettings = field(default_factory=ProviderSettings)


@dataclass(frozen=True)
class CacheConfig:
    """Provider-independent cache TTLs and staleness policy."""

    default_ttl_seconds: int = 3600
    price_ttl_seconds: int = 900
    nav_ttl_seconds: int = 3600
    history_ttl_seconds: int = 86400
    snapshot_ttl_seconds: int = 86400
    max_staleness_seconds: int = 604800
    cleanup_older_than_days: int = 30


@dataclass(frozen=True)
class QualityConfig:
    """Data-quality engine thresholds."""

    max_missing_fraction: float = 0.25
    max_duplicate_fraction: float = 0.02
    stale_price_days: int = 5
    outlier_zscore: float = 4.0
    min_history_points: int = 60
    max_return_jump: float = 0.50
    invalid_nav_min: float = 0.01
    allow_cache_fallback: bool = True


@dataclass(frozen=True)
class RefreshConfig:
    """Background job cadence (hours)."""

    market_data_hours: int = 6
    rankings_hours: int = 24
    metrics_hours: int = 24
    snapshots_hours: int = 24
    holdings_hours: int = 168
    cache_clean_hours: int = 24


@dataclass(frozen=True)
class ReportConfig:
    """Research report rendering options."""

    include_metrics_table: bool = True
    include_factor_scores: bool = True
    include_strengths_weaknesses: bool = True
    include_risk_summary: bool = True
    include_data_sources: bool = True
    max_universe_display: int = 50


@dataclass(frozen=True)
class ComparisonConfig:
    """Comparison engine behaviour."""

    max_securities: int = 10
    winner_metric_priority: Tuple[str, ...] = (
        "overall_score",
        "sharpe_ratio",
        "expense_ratio",
    )
    require_same_asset_class: bool = False


@dataclass(frozen=True)
class EvaluatorConfig:
    """Per-target-asset-class evaluator settings.

    ``universe`` is the curated default list of symbols an evaluator
    discovers when no search query is provided. ``provider_kind`` is the
    ``SecurityKind`` value the identity must carry for the provider
    chain to serve it (e.g. ``"etf"``, ``"mutual_fund"``).
    """

    universe: Tuple[str, ...] = ()
    provider_kind: str = "etf"
    max_candidates: int = 30
    default_exchange: Optional[str] = None


@dataclass(frozen=True)
class SecuritySelectionConfig:
    """Root configuration aggregating every section."""

    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    ranking: RankingConfig = field(default_factory=RankingConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    filters: FilterDefaultsConfig = field(default_factory=FilterDefaultsConfig)
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    refresh: RefreshConfig = field(default_factory=RefreshConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    comparison: ComparisonConfig = field(default_factory=ComparisonConfig)
    evaluators: Mapping[str, EvaluatorConfig] = field(default_factory=dict)

    def evaluator_config(self, target: TargetAssetClass) -> EvaluatorConfig | None:
        """Return the evaluator configuration for a given target asset class.

        Parameters
        ----------
        target:
            The target asset class to look up.

        Returns
        -------
        EvaluatorConfig | None
            The evaluator config, or ``None`` if not found.
        """
        return self.evaluators.get(target.value)


# ─────────────────────────────────────────────────────────────────────
# Loading machinery
# ─────────────────────────────────────────────────────────────────────

_ConfigT = TypeVar("_ConfigT", bound=type)

_SECTION_TYPES: Mapping[str, Type[Any]] = {
    "scoring": ScoringConfig,
    "ranking": RankingConfig,
    "optimization": OptimizationConfig,
    "filters": FilterDefaultsConfig,
    "providers": ProviderConfig,
    "cache": CacheConfig,
    "quality": QualityConfig,
    "refresh": RefreshConfig,
    "report": ReportConfig,
    "comparison": ComparisonConfig,
    "evaluators": EvaluatorConfig,  # special handling in _build_evaluators
}


def _coerce_tuple(value: Any) -> Any:
    """Recursively coerce YAML lists into tuples (keeps dataclasses frozen)."""
    if isinstance(value, list):
        return tuple(_coerce_tuple(v) for v in value)
    if isinstance(value, dict):
        return {k: _coerce_tuple(v) for k, v in value.items()}
    return value


def _build_section(section_name: str, raw: Mapping[str, Any], cls: Type[Any]) -> Any:
    """Instantiate one typed config section from a raw YAML mapping.

    Unknown keys are ignored so older YAML files remain forward
    compatible; missing keys fall back to the dataclass defaults.
    """
    valid_fields = {f.name for f in fields(cls)}
    kwargs: Dict[str, Any] = {}
    for key, value in raw.items():
        if key not in valid_fields:
            logger.warning("Ignoring unknown config key '%s.%s'", section_name, key)
            continue
        kwargs[key] = _coerce_tuple(value)
    return cls(**kwargs)


def _build_evaluators(raw: Mapping[str, Any]) -> Dict[str, EvaluatorConfig]:
    """Build the ``{target: EvaluatorConfig}`` map from YAML.

    Unlike the other sections, ``evaluators`` is keyed by target asset
    class (e.g. ``large_cap_equity``), each value being its own config
    mapping. Each sub-mapping is validated the same way as any section.
    """
    out: Dict[str, EvaluatorConfig] = {}
    for target, value in raw.items():
        if not isinstance(value, Mapping):
            raise ValueError(f"evaluators['{target}'] must be a mapping")
        out[target] = _build_section(f"evaluators.{target}", value, EvaluatorConfig)
    return out


def _load_from_mapping(raw: Mapping[str, Any]) -> SecuritySelectionConfig:
    """Build a :class:`SecuritySelectionConfig` from a parsed YAML mapping."""
    sections: Dict[str, Any] = {}
    for name, cls in _SECTION_TYPES.items():
        section_raw = raw.get(name, {})
        if not isinstance(section_raw, Mapping):
            raise ValueError(f"config section '{name}' must be a mapping")
        if name == "evaluators":
            sections[name] = _build_evaluators(section_raw)
        else:
            sections[name] = _build_section(name, section_raw, cls)
    return SecuritySelectionConfig(**sections)


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

_load_lock = threading.Lock()
_cached: Optional[SecuritySelectionConfig] = None


def load_config(path: Optional[Path] = None) -> SecuritySelectionConfig:
    """Load and parse the configuration from disk."""
    config_path = path or _CONFIG_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    except OSError as exc:
        raise ValueError(f"unable to read config file: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"malformed YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, Mapping):
        raise ValueError(f"config file {config_path} must contain a top-level mapping")
    return _load_from_mapping(raw)


def get_config() -> SecuritySelectionConfig:
    """Return the process-wide cached configuration (loaded on first use)."""
    global _cached
    with _load_lock:
        if _cached is None:
            _cached = load_config()
        return _cached


def reset_config_cache() -> None:
    """Drop the cached configuration (mainly for tests)."""
    global _cached
    with _load_lock:
        _cached = None

