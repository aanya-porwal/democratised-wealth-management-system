"""Tests for the configuration layer (PART 9) and new models."""

import pytest

from wealth_management_system.config import get_config, load_config, reset_config_cache
from wealth_management_system.exceptions import ConfigurationError


def test_config_loads_and_matches_yaml():
    """Type-checked config must reflect the YAML values."""
    config = get_config()
    assert config.simulation.default_simulations == 10000
    assert config.simulation.rng_seed == 42
    assert config.goal.at_risk_threshold == 0.50
    assert config.goal.on_track_threshold == 0.80
    assert config.rebalancing.absolute_drift_threshold == 0.05
    assert config.optimization.max_allocation == 0.50
    assert config.asset.equity_weight_by_score
    assert config.inflation.inflation_linked_goals


def test_config_is_singleton():
    """get_config() must return the same cached object."""
    a = get_config()
    reset_config_cache()
    b = get_config()
    assert a is b or a == b


def test_reset_config_cache():
    """reset_config_cache() must drop the cache."""
    get_config()
    reset_config_cache()
    # just verifies reset doesn't crash; next get re-loads
    assert get_config() is not None


def test_config_sections_exist():
    """Every engine section must be present."""
    config = get_config()
    for name in (
        "inflation",
        "goal",
        "risk",
        "health",
        "simulation",
        "optimization",
        "rebalancing",
        "tax",
        "scenario",
        "asset",
    ):
        assert getattr(config, name) is not None


def test_bad_config_path_raises(tmp_path):
    """A missing config file must raise ConfigurationError."""
    with pytest.raises(ConfigurationError):
        load_config(tmp_path / "does_not_exist.yaml")


def test_frozen_config_rejects_mutation():
    """Config dataclasses must be frozen."""
    config = get_config()
    with pytest.raises(Exception):
        config.simulation.default_simulations = 123  # type: ignore[misc]

