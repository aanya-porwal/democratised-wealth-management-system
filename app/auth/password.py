"""Password hashing — passlib + bcrypt."""

from __future__ import annotations

from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password with a fresh bcrypt salt."""
    if not plain or len(plain) < 8:
        raise ValueError("Password must be at least 8 characters")
    return _ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return _ctx.verify(plain, hashed)
    except ValueError:
        return False

