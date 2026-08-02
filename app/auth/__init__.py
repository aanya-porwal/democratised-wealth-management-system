"""Authentication package: passwords, JWT, RBAC dependencies."""

from app.auth.deps import get_current_user, get_current_user_optional, require_roles
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_payload,
)
from app.auth.password import hash_password, verify_password

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_token_payload",
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
]

