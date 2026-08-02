"""Portfolio endpoint tests — CRUD, holdings, snapshots."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
def portfolio_payload() -> dict:
    return {
        "name": "Main Portfolio",
        "description": "Primary investment portfolio",
    }


@pytest.mark.asyncio
async def test_create_portfolio(
    async_client: AsyncClient, db_session, default_user, auth_headers, portfolio_payload
) -> None:
    resp = await async_client.post("/api/v1/portfolio", json=portfolio_payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Main Portfolio"


@pytest.mark.asyncio
async def test_list_portfolios(
    async_client: AsyncClient, db_session, default_user, auth_headers, portfolio_payload
) -> None:
    await async_client.post("/api/v1/portfolio", json=portfolio_payload, headers=auth_headers)
    resp = await async_client.get("/api/v1/portfolio", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_add_holding(
    async_client: AsyncClient, db_session, default_user, auth_headers, portfolio_payload
) -> None:
    create_resp = await async_client.post(
        "/api/v1/portfolio", json=portfolio_payload, headers=auth_headers
    )
    portfolio_id = create_resp.json()["id"]

    holding_payload = {
        "asset_class": "equity_index_largecap",
        "market_value": 500000,
        "cost_basis": 450000,
    }
    resp = await async_client.post(
        f"/api/v1/portfolio/{portfolio_id}/holdings",
        json=holding_payload,
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["asset_class"] == "equity_index_largecap"
