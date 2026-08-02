"""Shared pytest fixtures and configuration management.

These fixtures keep the engine tests fast (small Monte Carlo paths) and
deterministic. The production config is loaded normally; tests that need
to mutate it use ``reset_config_cache``.
"""

from __future__ import annotations

import pytest

from wealth_management_system.config import reset_config_cache
from wealth_management_system.sample_users import build_all_sample_users


@pytest.fixture(autouse=True)
def _reset_config() -> None:
    """Reset the config cache before every test to avoid cross-test leaks."""
    reset_config_cache()
    yield
    reset_config_cache()


@pytest.fixture(scope="module")
def all_sample_users() -> list:
    """All sample users (ravi, meena + archetypes), built once per module."""
    return build_all_sample_users()


@pytest.fixture(scope="module")
def ravi() -> object:
    """Ravi Shankar — the canonical demo user."""
    return [u for u in build_all_sample_users() if u.name == "Ravi Shankar"][0]


@pytest.fixture(scope="module")
def priya() -> object:
    """Priya Parent — a user with strong foundations."""
    return [u for u in build_all_sample_users() if u.name == "Priya Parent"][0]

