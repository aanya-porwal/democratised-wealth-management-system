"""Authentication endpoints — register, login, logout, refresh tokens,
password reset, email verification.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.ratelimit import check_rate_limit
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter()


def _auth_service(session: Annotated[Session, Depends(get_db)]) -> AuthService:
    """Build an AuthService bound to the request-scoped session."""
    return AuthService(session)


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=201,
    summary="Create a new account",
    description="Registers a user and returns an authenticated token pair.",
)
def register(
    payload: RegisterRequest,
    request: Request,
    service: Annotated[AuthService, Depends(_auth_service)],
) -> LoginResponse:
    """Register a new user (rate-limited to 10/minute)."""
    check_rate_limit(request, key_prefix="rl:auth:register", spec="10/minute")
    user = service.register(payload)
    return service.login(payload.email, payload.password)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and obtain tokens",
    description="Validates credentials and returns an access + refresh token pair.",
)
def login(
    payload: LoginRequest,
    request: Request,
    service: Annotated[AuthService, Depends(_auth_service)],
) -> LoginResponse:
    """Log a user in (rate-limited to 10/minute)."""
    check_rate_limit(request, key_prefix="rl:auth:login", spec="10/minute")
    return service.login(payload.email, payload.password)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Rotate a refresh token",
    description="Exchanges a valid refresh token for a fresh access + refresh pair.",
)
def refresh(
    payload: RefreshRequest,
    service: Annotated[AuthService, Depends(_auth_service)],
) -> RefreshResponse:
    """Refresh (rotate) the token pair."""
    tokens = service.refresh(payload.refresh_token)
    return RefreshResponse(**tokens.model_dump())


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out and revoke tokens",
    description="Revokes the session: blacklists the access token and "
    "revokes the refresh token.",
)
def logout(
    payload: LogoutRequest,
    request: Request,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(_auth_service)],
) -> MessageResponse:
    """Log the current user out."""
    access_token = _bearer_token(request)
    service.logout(current, refresh_token=payload.refresh_token, access_token=access_token)
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    summary="Request a password reset",
    description="Creates a reset token. In production the token is emailed.",
)
def request_password_reset(
    payload: dict,
    service: Annotated[AuthService, Depends(_auth_service)],
) -> MessageResponse:
    """Request a password-reset token for an email address."""
    email = payload.get("email")
    if not email:
        from app.core.exceptions import ValidationError

        raise ValidationError("email is required", code="missing_email")
    service.request_password_reset(email)
    return MessageResponse(message="If the account exists, a reset link has been sent")


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    summary="Confirm a password reset",
    description="Applies a new password using a reset token.",
)
def confirm_password_reset(
    payload: dict,
    service: Annotated[AuthService, Depends(_auth_service)],
) -> MessageResponse:
    """Reset the password with a token + new password."""
    token = payload.get("token")
    new_password = payload.get("new_password")
    if not token or not new_password:
        from app.core.exceptions import ValidationError

        raise ValidationError("token and new_password are required", code="missing_fields")
    service.reset_password(token, new_password)
    return MessageResponse(message="Password has been reset")


@router.post(
    "/email-verification/request",
    response_model=MessageResponse,
    summary="Request an email-verification token",
    description="Creates a verification token for the current user.",
)
def request_email_verification(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(_auth_service)],
) -> MessageResponse:
    """Create an email-verification token for the authenticated user."""
    service.create_email_verification(current)
    return MessageResponse(message="If the account exists, a verification link has been sent")


@router.post(
    "/email-verification/confirm",
    response_model=MessageResponse,
    summary="Verify an email address",
    description="Marks the user's email as verified using a token.",
)
def confirm_email_verification(
    payload: dict,
    service: Annotated[AuthService, Depends(_auth_service)],
) -> MessageResponse:
    """Verify the user's email with a token."""
    token = payload.get("token")
    if not token:
        from app.core.exceptions import ValidationError

        raise ValidationError("token is required", code="missing_token")
    service.verify_email(token)
    return MessageResponse(message="Email verified successfully")


def _bearer_token(request: Request) -> str | None:
    """Extract the raw Bearer token (if any) from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return None

