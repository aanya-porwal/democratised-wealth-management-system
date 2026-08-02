"""User management endpoint tests — admin-only listing, role changes."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_admin(async_client: AsyncClient, db_session, admin_auth_headers) -> None:
    resp = await async_client.get("/api/v1/users", headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "pagination" in data


@pytest.mark.asyncio
async def test_list_users_unauthorized(async_client: AsyncClient, auth_headers) -> None:
    resp = await async_client.get("/api/v1/users", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_user_admin(async_client: AsyncClient, db_session, default_user, admin_auth_headers) -> None:
    resp = await async_client.get(f"/api/v1/users/{default_user.id}", headers=admin_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"
