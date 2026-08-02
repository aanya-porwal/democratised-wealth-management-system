"""Recommendation endpoint tests — generate, list, get, dismiss."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_recommendations(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    resp = await async_client.post("/api/v1/recommendations/generate", headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_recommendations(
    async_client: AsyncClient, db_session, default_user, auth_headers
) -> None:
    await async_client.post("/api/v1/recommendations/generate", headers=auth_headers)
    resp = await async_client.get("/api/v1/recommendations", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
