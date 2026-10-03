"""Authentication endpoint tests — register, login, refresh, logout, password reset."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(async_client: AsyncClient, db_session) -> None:
    payload = {
        "email": "newuser@example.com",
        "password": "StrongPass1!",
        "full_name": "New User",
    }
    resp = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    # Intended contract (app/schemas/auth.py LoginResponse + web/types/api.ts):
    # the token pair is nested under "tokens".
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login(async_client: AsyncClient, db_session, default_user) -> None:
    payload = {"email": "test@example.com", "password": "password123"}
    resp = await async_client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # LoginResponse nests the token pair (mirrors web/types/api.ts).
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, db_session, default_user) -> None:
    payload = {"email": "test@example.com", "password": "wrongpass"}
    resp = await async_client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh(async_client: AsyncClient, db_session, default_user) -> None:
    from app.auth.jwt import create_token_pair

    tokens = create_token_pair(subject=str(default_user.id), role=default_user.role.value)
    resp = await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, db_session, default_user, auth_headers) -> None:
    from app.auth.jwt import create_token_pair

    tokens = create_token_pair(subject=str(default_user.id), role=default_user.role.value)
    resp = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"


@pytest.mark.asyncio
async def test_password_reset_request(async_client: AsyncClient, db_session) -> None:
    resp = await async_client.post(
        "/api/v1/auth/password-reset/request", json={"email": "test@example.com"}
    )
    assert resp.status_code == 200
