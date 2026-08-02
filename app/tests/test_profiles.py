"""Profile endpoint tests — demographic, financial, behavioral profiles and risk assessment."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_full_profile(async_client: AsyncClient, db_session, default_user, auth_headers) -> None:
    resp = await async_client.get("/api/v1/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data


@pytest.mark.asyncio
async def test_upsert_user_profile(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    payload = {
        "name": "Test User",
        "age": 30,
        "date_of_birth": "1994-05-15",
        "dependents": 1,
        "life_stage": "wealth_building",
        "city": "Mumbai",
        "occupation": "Engineer",
    }
    resp = await async_client.put("/api/v1/profile/user", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test User"


@pytest.mark.asyncio
async def test_upsert_financial_profile(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    payload = {
        "monthly_income": 85000,
        "employment_type": "salaried_private",
        "income_stability": 0.85,
        "monthly_fixed_expenses": 35000,
        "monthly_variable_expenses": 20000,
        "emergency_fund_months": 3.0,
        "existing_investments": 100000,
        "tax_bracket_percent": 20,
    }
    resp = await async_client.put("/api/v1/profile/financial", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["monthly_income"] == 85000


@pytest.mark.asyncio
async def test_upsert_behavioral_profile(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    payload = {
        "risk_tolerance": "aggressive",
        "drawdown_reaction_score": 4,
        "has_invested_before": True,
        "financial_literacy_score": 3,
        "loss_aversion_score": 2,
    }
    resp = await async_client.put("/api/v1/profile/behavioral", json=payload, headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_risk_assessment(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    resp = await async_client.get("/api/v1/profile/risk", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "final_score_100" in data
