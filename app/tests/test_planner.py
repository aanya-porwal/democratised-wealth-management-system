"""Planner endpoint tests — the full explained financial plan."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_build_plan(async_client: AsyncClient, db_session, default_user, auth_headers) -> None:
    resp = await async_client.get("/api/v1/planner/plan", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # A plan will have a summary or a user_name field
    assert "summary" in data or "user_name" in data
