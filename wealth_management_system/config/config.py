"""Typed configuration loader for the wealth management system.

Loads ``config.yaml`` once per process and exposes the values through a
set of frozen dataclasses. Every engine that needs a tunable constant
should read it from here rather than hardcoding it.

Design notes
------------
* The loader is deliberately dependency-light: it only requires
  ``PyYAML`` (already in the environment).
* Nested YAML dictionaries are mapped to nested frozen dataclasses so
  callers get attribute access (``config.simulation.simulations``) and
  typos fail fast with an ``AttributeError`` rather than a ``KeyError``.
* ``get_config`` caches the loaded object so repeated calls are cheap and
  consistent within one process. Tests can bypass the cache with
  ``load_config``.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, TypeVar

import yaml

from wealth_management_system.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config.yaml"

# ─────────────────────────────────────────────────────────────────────
# Typed configuration sections
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class InflationConfig:
    """Long-run inflation assumptions."""

    default_rate: float = 0.06
    inflation_linked_goals: Tuple[str, ...] = ()
    nominal_goals: Tuple[str, ...] = ()


@dataclass(frozen=True)
class GoalConfig:
    """Goal engine assumptions."""

    default_expected_return: float = 0.07
    default_inflation: float = 0.06
    feasibility_threshold: float = 0.60
    on_track_threshold: float = 0.80
    at_risk_threshold: float = 0.50


@dataclass(frozen=True)
class RiskConfig:
    """Risk scoring weights and category bands."""

    capacity_weights: Mapping[str, float] = field(default_factory=dict)
    tolerance_stated_weight: float = 0.40
    tolerance_drawdown_weight: float = 0.40
    tolerance_blend: float = 0.45
    capacity_blend: float = 0.55
    categories: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthConfig:
    """Financial health score factor weights and caps."""

    factor_weights: Mapping[str, float] = field(default_factory=dict)
    ef_missing_cap: int = 39
    ef_building_cap: int = 69
    excellent_min: int = 80
    good_min: int = 60
    fair_min: int = 40
    poor_min: int = 20


@dataclass(frozen=True)
class SimulationConfig:
    """Monte Carlo simulation parameters."""

    default_simulations: int = 10000
    min_simulations: int = 1000
    max_simulations: int = 100000
    default_mean_return: float = 0.07
    default_volatility: float = 0.12
    default_inflation: float = 0.06
    rng_seed: int = 42
    percentiles: Tuple[float, ...] = (0.05, 0.25, 0.50, 0.75, 0.95)
    histogram_bins: int = 50


@dataclass(frozen=True)
class OptimizationConfig:
    """Mean-variance optimization constraints."""

    default_risk_free_rate: float = 0.055
    min_allocation: float = 0.0
    max_allocation: float = 0.50
    max_volatility: float = 0.16
    min_liquidity_score: float = 0.0
    liquidity_penalty: float = 0.02
    min_variance_floor: float = 1.0e-6


@dataclass(frozen=True)
class RebalancingConfig:
    """Rebalancing drift thresholds and cost assumptions."""

    absolute_drift_threshold: float = 0.05
    relative_drift_threshold: float = 0.20
    min_trade_fraction: float = 0.01
    transaction_cost_rate: float = 0.001
    capital_gains_tax_rate: float = 0.10
    min_portfolio_value: float = 10000


@dataclass(frozen=True)
class TaxConfig:
    """Tax assumptions."""

    equity_ltcg_rate: float = 0.10
    equity_stcg_rate: float = 0.15
    debt_rate_uses_slab: bool = True
    sec_80c_limit: float = 150000
    sec_80ccd_1b_limit: float = 50000
    equity_ltcg_exemption: float = 100000
    sgb_interest_rate: float = 0.025


@dataclass(frozen=True)
class ScenarioConfig:
    """Scenario analysis default severities."""

    salary_increase_pct: float = 0.15
    salary_decrease_pct: float = 0.15
    market_crash_drawdown: float = 0.30
    emergency_expense_months: float = 3.0


@dataclass(frozen=True)
class AssetConfig:
    """Strategic allocation glidepath and per-instrument caps."""

    equity_weight_by_score: Tuple[Tuple[float, float], ...] = ()
    debt_default_share: float = 0.80
    gold_share: float = 0.10
    cash_share: float = 0.10
    max_elss_fraction: float = 0.25
    max_ppf_fraction: float = 0.25
    max_nps_fraction: float = 0.15
    max_epf_fraction: float = 0.20
    max_fixed_deposit_fraction: float = 0.30
    max_cash_fraction: float = 0.10
    max_reit_fraction: float = 0.10
    max_international_fraction: float = 0.20


@dataclass(frozen=True)
class WealthConfig:
    """Root configuration aggregating every section."""

    inflation: InflationConfig = field(default_factory=InflationConfig)
    goal: GoalConfig = field(default_factory=GoalConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    rebalancing: RebalancingConfig = field(default_factory=RebalancingConfig)
    tax: TaxConfig = field(default_factory=TaxConfig)
    scenario: ScenarioConfig = field(default_factory=ScenarioConfig)
    asset: AssetConfig = field(default_factory=AssetConfig)


# ─────────────────────────────────────────────────────────────────────
# Loading machinery
# ─────────────────────────────────────────────────────────────────────

_ConfigT = TypeVar("_ConfigT", bound=type)

# mapping of section name -> dataclass type
_SECTION_TYPES: Mapping[str, Type[Any]] = {
    "inflation": InflationConfig,
    "goal": GoalConfig,
    "risk": RiskConfig,
    "health": HealthConfig,
    "simulation": SimulationConfig,
    "optimization": OptimizationConfig,
    "rebalancing": RebalancingConfig,
    "tax": TaxConfig,
    "scenario": ScenarioConfig,
    "asset": AssetConfig,
}


def _coerce_tuple(value: Any) -> Any:
    """Recursively coerce YAML lists into tuples (keeps dataclasses frozen)."""
    if isinstance(value, list):
        return tuple(_coerce_tuple(v) for v in value)
    if isinstance(value, dict):
        return {k: _coerce_tuple(v) for k, v in value.items()}
    return value


def _build_section(
    section_name: str, raw: Mapping[str, Any], cls: Type[Any]
) -> Any:
    """Instantiate one typed config section from a raw YAML mapping.

    Unknown keys are ignored so older YAML files remain forward
    compatible; missing keys fall back to the dataclass defaults.
    """
    valid_fields = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    kwargs: Dict[str, Any] = {}
    for key, value in raw.items():
        if key not in valid_fields:
            logger.warning(
                "Ignoring unknown config key '%s.%s'", section_name, key
            )
            continue
        kwargs[key] = _coerce_tuple(value)
    return cls(**kwargs)


def _load_from_mapping(raw: Mapping[str, Any]) -> WealthConfig:
    """Build a :class:`WealthConfig` from a parsed YAML mapping."""
    sections: Dict[str, Any] = {}
    for name, cls in _SECTION_TYPES.items():
        section_raw = raw.get(name, {})
        if not isinstance(section_raw, Mapping):
            raise ConfigurationError(
                f"config section '{name}' must be a mapping, got "
                f"{type(section_raw).__name__}"
            )
        sections[name] = _build_section(name, section_raw, cls)
    return WealthConfig(**sections)


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

_load_lock = threading.Lock()
_cached: Optional[WealthConfig] = None


def load_config(path: Optional[Path] = None) -> WealthConfig:
    """Load and parse the configuration from disk.

    Parameters
    ----------
    path:
        Path to a ``config.yaml`` file. Defaults to the packaged
        ``config/config.yaml``.

    Returns
    -------
    WealthConfig
        The fully typed configuration object.

    Raises
    ------
    ConfigurationError
        If the file is missing, malformed, or a section is not a mapping.
    """
    config_path = path or _CONFIG_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    except OSError as exc:  # pragma: no cover - depends on filesystem
        raise ConfigurationError(
            f"unable to read config file: {config_path}"
        ) from exc
    except yaml.YAMLError as exc:  # pragma: no cover - depends on content
        raise ConfigurationError(f"malformed YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, Mapping):
        raise ConfigurationError(
            f"config file {config_path} must contain a top-level mapping"
        )
    return _load_from_mapping(raw)


def get_config() -> WealthConfig:
    """Return the process-wide cached configuration (loaded on first use).

    The result is memoised so all engines agree on one consistent set of
    constants for the life of the process.
    """
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

