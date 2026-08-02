"""Strategic allocation endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_compute_allocation(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    payload = {"horizon_years": 15, "liquidity_need": "low"}
    resp = await async_client.post(
        "/api/v1/allocation", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "buckets" in data
    assert "risk_score" in data
    assert "explanation" in data
    assert len(data["buckets"]) > 0
    # weights should sum to ~1.0
    total = sum(b["weight"] for b in data["buckets"])
    assert abs(total - 1.0) < 0.02
