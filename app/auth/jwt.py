"""JWT creation and validation (PyJWT).

* Access tokens are short-lived (30 min default) and carry the user id,
  role, token id (``jti``) and type.
* Refresh tokens are longer-lived and are validated against the DB
  before being rotated (see ``AuthService``).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import settings
from app.core.exceptions import AuthenticationError

_ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_token(
    *,
    subject: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    """Create a JWT and return (token, jti, expires_at)."""
    jti = str(uuid.uuid4())
    now = _now()
    expires_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)
    return token, jti, expires_at


def create_access_token(*, subject: str, role: str, extra: dict[str, Any] | None = None):
    """Create a short-lived access token."""
    return _create_token(
        subject=subject,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra=extra,
    )


def create_refresh_token(*, subject: str, role: str, extra: dict[str, Any] | None = None):
    """Create a long-lived refresh token."""
    return _create_token(
        subject=subject,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        extra=extra,
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Decode + verify a JWT. Raises AuthenticationError on any failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired", code="token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid token", code="invalid_token") from exc

    if expected_type and payload.get("type") != expected_type:
        raise AuthenticationError(
            f"Expected a {expected_type} token", code="wrong_token_type"
        )
    if not payload.get("sub") or not payload.get("jti"):
        raise AuthenticationError("Token is missing required claims", code="invalid_token")
    return payload


def get_token_payload(token: str) -> dict[str, Any]:
    """Alias returning the verified payload (access tokens)."""
    return decode_token(token, expected_type="access")


def create_token_pair(*, subject: str, role: str, extra: dict[str, Any] | None = None) -> dict:
    """Create a signed (access, refresh) token pair.

    Returns a dict with the two JWT strings plus their metadata:
    ``{"access_token", "refresh_token", "access_jti", "refresh_jti",
    "expires_in"}``. ``expires_in`` is the access-token lifetime in
    seconds and is what :class:`app.schemas.auth.TokenPair` expects.
    """
    access_token, access_jti, access_exp = create_access_token(
        subject=subject, role=role, extra=extra
    )
    refresh_token, refresh_jti, _ = create_refresh_token(
        subject=subject, role=role, extra=extra
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_jti": access_jti,
        "refresh_jti": refresh_jti,
        "expires_in": int(settings.access_token_expire_seconds),
    }

