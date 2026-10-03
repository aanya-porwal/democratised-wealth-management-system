"""Auth service — register, login, logout, refresh, password reset,
email verification. Orchestrates the user repository and JWT helpers.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth.jwt import create_token_pair, decode_token
from app.auth.password import hash_password, verify_password
from app.config.settings import settings
from app.core import cache
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.auth_token import EmailVerificationToken, PasswordResetToken, RefreshToken
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, RegisterRequest, TokenPair


class AuthService:
    """Encapsulates all authentication workflows."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    # ── register ────────────────────────────────────────────────────

    def register(self, payload: RegisterRequest) -> User:
        if self.users.get_by_email(payload.email) is not None:
            raise ConflictError("An account with this email already exists", code="email_taken")
        user = self.users.create(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=Role.USER,
        )
        return user

    # ── login ───────────────────────────────────────────────────────

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password", code="invalid_credentials")
        if not user.is_active or user.is_deleted:
            raise AuthenticationError("Account is disabled", code="account_disabled")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        pair = create_token_pair(subject=str(user.id), role=user.role.value)
        tokens = TokenPair(
            access_token=pair["access_token"],
            refresh_token=pair["refresh_token"],
            expires_in=pair["expires_in"],
        )
        # persist refresh token (hash, never raw); jti comes from the
        # signed payload so rotation can find the exact DB row later.
        token_hash = hashlib.sha256(pair["refresh_token"].encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.refresh_token_expire_seconds)
        self.users.create_refresh_token(
            user_id=user.id,
            jti=pair["refresh_jti"],
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.commit()
        return tokens

    def login(self, email: str, password: str) -> LoginResponse:
        user = self.authenticate(email, password)
        tokens = self.issue_tokens(user)
        return LoginResponse(
            tokens=tokens, user_id=user.id, role=user.role.value, full_name=user.full_name
        )

    # ── refresh ─────────────────────────────────────────────────────

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except AuthenticationError as exc:
            raise AuthenticationError("Invalid refresh token", code="invalid_refresh_token") from exc

        if cache.cache.is_jwt_blacklisted(payload["jti"]):
            raise AuthenticationError("Refresh token revoked", code="token_revoked")

        user = self.users.get(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthenticationError("User not found", code="user_inactive")

        # rotate: revoke old, issue new
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        existing = self.users.get_refresh_token(payload["jti"])
        if existing is not None and existing.revoked_at is None:
            self.users.revoke_refresh_token(existing)

        new_pair = create_token_pair(subject=str(user.id), role=user.role.value)
        tokens = TokenPair(
            access_token=new_pair["access_token"],
            refresh_token=new_pair["refresh_token"],
            expires_in=new_pair["expires_in"],
        )
        new_hash = hashlib.sha256(new_pair["refresh_token"].encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.refresh_token_expire_seconds)
        self.users.create_refresh_token(
            user_id=user.id,
            jti=new_pair["refresh_jti"],
            token_hash=new_hash,
            expires_at=expires_at,
        )
        self.session.commit()
        return tokens

    # ── logout ──────────────────────────────────────────────────────

    def logout(
        self,
        user: User,
        refresh_token: str | None = None,
        access_token: str | None = None,
    ) -> None:
        """Revoke the user's session credentials.

        * Blacklists the current access token (by jti) so it cannot be
          reused for its remaining lifetime.
        * Revokes the provided refresh token when given.
        * Always clears every outstanding refresh token for the user.
        """
        if access_token:
            try:
                payload = decode_token(access_token, expected_type="access")
                cache.cache.blacklist_access_jti(payload["jti"])
            except AuthenticationError:
                pass  # already invalid/expired — nothing to blacklist

        if refresh_token:
            try:
                payload = decode_token(refresh_token, expected_type="refresh")
                existing = self.users.get_refresh_token(payload["jti"])
                if existing is not None:
                    self.users.revoke_refresh_token(existing)
            except AuthenticationError:
                pass

        # a logout ends the whole session: rotate every outstanding token.
        self.users.revoke_all_refresh_tokens(user.id)
        self.session.commit()

    # ── password reset (structure) ──────────────────────────────────

    def request_password_reset(self, email: str) -> str | None:
        """Create a reset token. Returns the token (in production this is emailed)."""
        user = self.users.get_by_email(email)
        if user is None:
            # do not reveal whether the account exists — behave as if sent.
            return None
        token = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        self.session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hashed,
                expires_at=expires_at,
            )
        )
        self.session.commit()
        return token

    def reset_password(self, token: str, new_password: str) -> None:
        hashed = hashlib.sha256(token.encode()).hexdigest()
        record = (
            self.session.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == hashed)
            .first()
        )
        if record is None or record.expires_at < datetime.now(timezone.utc) or record.used_at is not None:
            raise ValidationError("Reset token is invalid or expired", code="invalid_reset_token")
        user = self.users.get(record.user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        user.password_hash = hash_password(new_password)
        record.used_at = datetime.now(timezone.utc)
        self.users.revoke_all_refresh_tokens(user.id)
        self.session.commit()

    # ── email verification (structure) ──────────────────────────────

    def create_email_verification(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
        self.session.add(
            EmailVerificationToken(
                user_id=user.id, token_hash=hashed, expires_at=expires_at
            )
        )
        self.session.commit()
        return token

    def verify_email(self, token: str) -> User:
        hashed = hashlib.sha256(token.encode()).hexdigest()
        record = (
            self.session.query(EmailVerificationToken)
            .filter(EmailVerificationToken.token_hash == hashed)
            .first()
        )
        if record is None or record.expires_at < datetime.now(timezone.utc) or record.used_at is not None:
            raise ValidationError("Verification token is invalid or expired", code="invalid_verify_token")
        user = self.users.get(record.user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        user.is_email_verified = True
        record.used_at = datetime.now(timezone.utc)
        self.session.commit()
        return user

