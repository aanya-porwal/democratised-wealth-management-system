"""Goal endpoint tests — CRUD, engine analysis, progress snapshots."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
def goal_payload() -> dict:
    return {
        "name": "Retirement",
        "goal_type": "retirement",
        "priority": "critical",
        "target_amount": 20000000,
        "target_date": "2045-01-01",
        "current_savings_for_goal": 500000,
        "current_monthly_contribution": 15000,
    }


@pytest.mark.asyncio
async def test_create_goal(
    async_client: AsyncClient, db_session, default_user, auth_headers, goal_payload
) -> None:
    resp = await async_client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["goal_type"] == "retirement"


@pytest.mark.asyncio
async def test_list_goals(
    async_client: AsyncClient, db_session, default_user, auth_headers, goal_payload
) -> None:
    await async_client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    resp = await async_client.get("/api/v1/goals", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_analyse_all_goals(
    async_client: AsyncClient, db_session, default_user, auth_headers, goal_payload
) -> None:
    await async_client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    resp = await async_client.get("/api/v1/goals/analysis", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    if data:
        assert "goal_type" in data[0]
        assert "probability_of_success" in data[0]
