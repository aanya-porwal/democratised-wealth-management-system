"""Reusable FastAPI dependencies.

This package re-exports the auth/RBAC dependencies and provides the
session/rate-limit helpers used across every router, so route modules
never import directly from the internals.
"""

from app.auth.deps import (
    bearer_scheme,
    get_current_user,
    get_current_user_optional,
    require_roles,
)
from app.core.ratelimit import check_rate_limit
from app.database.session import get_db

__all__ = [
    "bearer_scheme",
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
    "get_db",
    "check_rate_limit",
]

