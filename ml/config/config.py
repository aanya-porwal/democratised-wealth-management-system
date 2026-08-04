"""Typed configuration loader for the Intelligent Learning & Simulation Platform.

Loads ``config.yaml`` once per process and exposes values through a set
of frozen dataclasses — mirroring the pattern used by
``security_selection.config`` and ``wealth_management_system.config``.
Every engine in the platform reads its tunable constants from here.

Design notes
------------
* Dependency-light: only requires ``PyYAML`` (already a dependency).
* Nested YAML maps to nested frozen dataclasses so callers get attribute
  access and typos fail fast.
* ``get_config`` caches the loaded object per process; tests can bypass
  the cache with ``load_config`` and ``reset_config_cache``.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple, Type, TypeVar

import yaml

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "config.yaml"


# ─────────────────────────────────────────────────────────────────────
# Typed configuration sections
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReproducibilityConfig:
    """Reproducibility controls."""

    seed: int = 42
    require_seed: bool = True


@dataclass(frozen=True)
class IncomeConfig:
    """Lognormal income distribution parameters."""

    log_mean: float = 10.5
    log_std: float = 0.85
    min_monthly: float = 8000.0
    max_monthly: float = 5000000.0


@dataclass(frozen=True)
class CorrelationConfig:
    """Gaussian copula correlation structure."""

    variables: Tuple[str, ...] = ()
    matrix: Tuple[Tuple[float, ...], ...] = ()


@dataclass(frozen=True)
class PopulationConfig:
    """Synthetic population generation parameters."""

    default_size: int = 100000
    city_tiers: Mapping[str, float] = field(default_factory=dict)
    age_range: Tuple[int, int] = (18, 80)
    gender_share_female: float = 0.48
    income: IncomeConfig = field(default_factory=IncomeConfig)
    correlation: CorrelationConfig = field(default_factory=CorrelationConfig)


@dataclass(frozen=True)
class PersonaConfig:
    """Persona archetype generation parameters."""

    n_archetypes: int = 24
    variations_per_archetype: int = 500


@dataclass(frozen=True)
class LifeEventsConfig:
    """Probabilistic life event parameters."""

    promotion_probability: float = 0.12
    marriage_probability: float = 0.06
    childbirth_probability: float = 0.08
    house_purchase_probability: float = 0.04
    vehicle_purchase_probability: float = 0.06
    inheritance_probability: float = 0.02
    medical_emergency_probability: float = 0.10
    job_loss_probability: float = 0.05
    career_switch_probability: float = 0.03
    business_success_probability: float = 0.15
    business_failure_probability: float = 0.10
    retirement_age: int = 60
    mortality_base: float = 0.004


@dataclass(frozen=True)
class MarketConfig:
    """Market simulation parameters."""

    assets: Tuple[str, ...] = ()
    annual_returns: Mapping[str, float] = field(default_factory=dict)
    annual_vols: Mapping[str, float] = field(default_factory=dict)
    history_years: int = 15
    fetch_real: bool = True
    static_seed_path: str = "data/static_market_seed.csv"


@dataclass(frozen=True)
class RecommendationConfig:
    """Recommendation & interaction simulation parameters."""

    categories: Tuple[str, ...] = ()
    outcomes: Tuple[str, ...] = ()
    acceptance: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FeatureEngineeringConfig:
    """Feature engineering families and lookback."""

    families: Tuple[str, ...] = ()
    lookback_steps: int = 12


@dataclass(frozen=True)
class DatasetConfig:
    """Dataset split and export configuration."""

    train_fraction: float = 0.70
    validation_fraction: float = 0.15
    test_fraction: float = 0.15
    formats: Tuple[str, ...] = ()
    database: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrainingConfig:
    """Training tasks, learners and hyperparameters."""

    tasks: Mapping[str, str] = field(default_factory=dict)
    learners: Mapping[str, bool] = field(default_factory=dict)
    cv_folds: int = 5
    hyperparameters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationConfig:
    """Model selection criteria."""

    ranking_metric: str = "auc"
    regression_metric: str = "rmse"
    maximize: bool = True


@dataclass(frozen=True)
class ExperimentsConfig:
    """Experiment tracking (MLflow + local fallback)."""

    tracking_uri: str = ""
    experiment_name: str = "wealth_ml_platform"
    artifact_dir: str = "experiments"
    registry_dir: str = "models/registry"


@dataclass(frozen=True)
class ShadowConfig:
    """Shadow deployment behaviour."""

    store: bool = True
    store_rule_output: bool = True


@dataclass(frozen=True)
class DataQualityConfig:
    """Data quality thresholds."""

    max_missing_fraction: float = 0.25
    max_duplicate_fraction: float = 0.02


@dataclass(frozen=True)
class MonitoringConfig:
    """Monitoring and drift detection."""

    psi_threshold: float = 0.2
    data_quality: DataQualityConfig = field(default_factory=DataQualityConfig)


@dataclass(frozen=True)
class MLConfig:
    """Root configuration aggregating every section."""

    reproducibility: ReproducibilityConfig = field(default_factory=ReproducibilityConfig)
    population: PopulationConfig = field(default_factory=PopulationConfig)
    persona: PersonaConfig = field(default_factory=PersonaConfig)
    life_events: LifeEventsConfig = field(default_factory=LifeEventsConfig)
    market: MarketConfig = field(default_factory=MarketConfig)
    recommendation: RecommendationConfig = field(default_factory=RecommendationConfig)
    feature_engineering: FeatureEngineeringConfig = field(default_factory=FeatureEngineeringConfig)
    datasets: DatasetConfig = field(default_factory=DatasetConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    experiments: ExperimentsConfig = field(default_factory=ExperimentsConfig)
    shadow: ShadowConfig = field(default_factory=ShadowConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)


# ─────────────────────────────────────────────────────────────────────
# Loading machinery
# ─────────────────────────────────────────────────────────────────────

_ConfigT = TypeVar("_ConfigT", bound=type)

_SECTION_TYPES: Mapping[str, Type[Any]] = {
    "reproducibility": ReproducibilityConfig,
    "population": PopulationConfig,
    "persona": PersonaConfig,
    "life_events": LifeEventsConfig,
    "market": MarketConfig,
    "recommendation": RecommendationConfig,
    "feature_engineering": FeatureEngineeringConfig,
    "datasets": DatasetConfig,
    "training": TrainingConfig,
    "evaluation": EvaluationConfig,
    "experiments": ExperimentsConfig,
    "shadow": ShadowConfig,
    "monitoring": MonitoringConfig,
}


def _coerce_tuple(value: Any) -> Any:
    """Recursively coerce YAML lists into tuples (keeps dataclasses frozen)."""
    if isinstance(value, list):
        return tuple(_coerce_tuple(v) for v in value)
    if isinstance(value, dict):
        return {k: _coerce_tuple(v) for k, v in value.items()}
    return value


def _build_section(section_name: str, raw: Mapping[str, Any], cls: Type[Any]) -> Any:
    """Instantiate one typed config section from a raw YAML mapping."""
    valid_fields = {f.name for f in fields(cls)}
    kwargs: Dict[str, Any] = {}
    for key, value in raw.items():
        if key not in valid_fields:
            logger.warning("Ignoring unknown config key '%s.%s'", section_name, key)
            continue
        kwargs[key] = _coerce_tuple(value)
    return cls(**kwargs)


def _load_from_mapping(raw: Mapping[str, Any]) -> MLConfig:
    """Build a :class:`MLConfig` from a parsed YAML mapping."""
    sections: Dict[str, Any] = {}
    for name, cls in _SECTION_TYPES.items():
        section_raw = raw.get(name, {})
        if not isinstance(section_raw, Mapping):
            raise ValueError(f"config section '{name}' must be a mapping")
        sections[name] = _build_section(name, section_raw, cls)
    return MLConfig(**sections)


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────

_load_lock = threading.Lock()
_cached: Optional[MLConfig] = None


def load_config(path: Optional[Path] = None) -> MLConfig:
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


def get_config() -> MLConfig:
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
