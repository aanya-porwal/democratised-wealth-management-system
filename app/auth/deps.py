"""FastAPI dependencies for authentication and role-based access control.

Usage::

    @router.get("/me")
    def me(current: User = Depends(get_current_user)) -> ...:

    @router.get("/admin")
    def admin(current: User = Depends(require_roles(Role.ADMIN))) -> ...:
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.core import cache
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.database import get_db
from app.models.user import Role, User

bearer_scheme = HTTPBearer(auto_error=False)


def _load_user(session: Session, user_id: str) -> User:
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise AuthenticationError("Invalid user id in token", code="invalid_token") from exc
    user = session.get(User, uid)
    if user is None or not user.is_active or user.is_deleted:
        raise AuthenticationError("User not found or inactive", code="user_inactive")
    return user


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the authenticated user from the Bearer access token."""
    if credentials is None:
        raise AuthenticationError("Missing authentication token", code="missing_token")

    payload = decode_token(credentials.credentials, expected_type="access")

    # Reject tokens that were revoked at logout.
    if cache.cache.is_jwt_blacklisted(payload["jti"]):
        raise AuthenticationError("Token has been revoked", code="token_revoked")

    return _load_user(session, payload["sub"])


def get_current_user_optional(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Resolve the user if a valid token is present, else return None."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        if cache.cache.is_jwt_blacklisted(payload["jti"]):
            return None
        return _load_user(session, payload["sub"])
    except AuthenticationError:
        return None


def require_roles(*roles: Role) -> Callable:
    """Return a dependency enforcing that the user has one of ``roles``."""

    def _dependency(current: Annotated[User, Depends(get_current_user)]) -> User:
        if current.role not in roles:
            raise ForbiddenError(
                "You do not have permission to access this resource",
                code="insufficient_role",
            )
        return current

    return _dependency

