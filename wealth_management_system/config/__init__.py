"""Configuration package for the wealth management system.

Centralises every tunable constant (returns, inflation, risk thresholds,
asset constraints, tax assumptions, simulation parameters) into a single
typed configuration object loaded from ``config.yaml``.

Importing this package has no side effects; call :func:`get_config` to
load (and cache) the configuration once per process.
"""

from wealth_management_system.config.config import (
    AssetConfig,
    GoalConfig,
    HealthConfig,
    InflationConfig,
    OptimizationConfig,
    RebalancingConfig,
    RiskConfig,
    ScenarioConfig,
    SimulationConfig,
    TaxConfig,
    WealthConfig,
    get_config,
    load_config,
    reset_config_cache,
)

__all__ = [
    "AssetConfig",
    "GoalConfig",
    "HealthConfig",
    "InflationConfig",
    "OptimizationConfig",
    "RebalancingConfig",
    "RiskConfig",
    "ScenarioConfig",
    "SimulationConfig",
    "TaxConfig",
    "WealthConfig",
    "get_config",
    "load_config",
    "reset_config_cache",
]

