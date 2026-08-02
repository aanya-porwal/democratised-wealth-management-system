"""Authentication request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Payload to create a new account."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "ravi@example.com",
            "password": "StrongPass123!",
            "full_name": "Ravi Shankar",
        }
    })

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def _validate_password_strength(cls, value: str) -> str:
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit")
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter")
        return value


class LoginRequest(BaseModel):
    """Payload to authenticate."""

    model_config = ConfigDict(json_schema_extra={"example": {"email": "ravi@example.com", "password": "StrongPass123!"}})

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenPair(BaseModel):
    """An access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class LoginResponse(BaseModel):
    """Successful authentication response."""

    tokens: TokenPair
    user_id: uuid.UUID
    role: str
    full_name: str


class RefreshRequest(BaseModel):
    """Payload to exchange a refresh token for a new pair."""

    refresh_token: str


class RefreshResponse(TokenPair):
    """A rotated token pair."""


class LogoutRequest(BaseModel):
    """Payload to revoke tokens on logout."""

    refresh_token: str | None = None

