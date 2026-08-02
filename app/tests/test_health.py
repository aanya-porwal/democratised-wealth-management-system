"""Financial health score endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_compute_health_score(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    resp = await async_client.post("/api/v1/health-score", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "grade" in data
    assert 0 <= data["score"] <= 100


@pytest.mark.asyncio
async def test_latest_health_scores(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    await async_client.post("/api/v1/health-score", headers=auth_headers)
    resp = await async_client.get("/api/v1/health-score/latest", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
