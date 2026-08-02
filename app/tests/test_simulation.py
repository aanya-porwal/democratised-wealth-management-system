"""Simulation and scenario endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_run_simulation(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    payload = {
        "expected_return": 0.12,
        "volatility": 0.18,
        "monthly_investment": 15000,
        "inflation": 0.06,
        "horizon_years": 20,
        "initial_corpus": 500000,
        "target_amount": 20000000,
        "simulations": 1000,
    }
    resp = await async_client.post("/api/v1/simulation", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "statistics" in data


@pytest.mark.asyncio
async def test_run_scenario(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    payload = {
        "scenario_type": "salary_increase",
        "income_multiplier": 1.15,
        "simulations": 1000,
    }
    resp = await async_client.post("/api/v1/scenarios", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "summary" in data
