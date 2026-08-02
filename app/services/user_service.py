"""User service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Admin-facing user workflows (lookup, role management, listing)."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def get(self, user_id: uuid.UUID) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found", code="user_not_found")
        return user

    def list_users(self, *, skip: int = 0, limit: int = 50, search: str | None = None):
        return self.users.list_paginated(skip=skip, limit=limit, search=search)

    def count_users(self, search: str | None = None) -> int:
        return self.users.count_all(search=search)

    def set_role(self, user_id: uuid.UUID, role: str) -> User:
        from app.models.user import Role

        user = self.get(user_id)
        try:
            new_role = Role(role)
        except ValueError as exc:
            raise NotFoundError(f"Unknown role: {role}", code="invalid_role") from exc
        return self.users.set_role(user, new_role)

