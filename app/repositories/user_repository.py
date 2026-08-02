"""User repository."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select

from app.models.auth_token import RefreshToken
from app.models.user import Role, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Persistence for users, auth tokens and lookups."""

    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.get_by(email=email)

    def get_by_phone(self, phone: str) -> User | None:
        return self.get_by(phone=phone)

    def get_by_email_or_phone(self, email: str, phone: str | None = None) -> User | None:
        stmt = select(User).where(
            or_(User.email == email, User.phone == phone if phone else False)
        )
        return self.session.execute(stmt).scalars().first()

    def list_paginated(self, *, skip: int, limit: int, search: str | None = None):
        stmt = select(User)
        if search:
            stmt = stmt.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )
        return list(self.session.execute(stmt.offset(skip).limit(limit)).scalars().all())

    def count_all(self, search: str | None = None) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(User)
        if search:
            stmt = stmt.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )
        return int(self.session.execute(stmt).scalar_one())

    def set_role(self, user: User, role: Role) -> User:
        user.role = role
        self.session.flush()
        return user

    # ── refresh tokens ─────────────────────────────────────────────

    def create_refresh_token(
        self, user_id: uuid.UUID, jti: str, token_hash: str, expires_at
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id, jti=jti, token_hash=token_hash, expires_at=expires_at
        )
        self.session.add(token)
        self.session.flush()
        return token

    def get_refresh_token(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        return self.session.execute(stmt).scalars().first()

    def revoke_refresh_token(self, token: RefreshToken) -> None:
        from datetime import datetime, timezone

        token.revoked_at = datetime.now(timezone.utc)
        self.session.flush()

    def revoke_all_refresh_tokens(self, user_id: uuid.UUID) -> None:
        from datetime import datetime, timezone

        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
        tokens = self.session.execute(stmt).scalars().all()
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)
        self.session.flush()

