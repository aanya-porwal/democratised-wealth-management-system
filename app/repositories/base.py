"""Generic SQLAlchemy repository base.

Implements the standard CRUD operations plus soft-delete awareness.
Every concrete repository extends this with domain-specific queries.

Uses SQLAlchemy 2.0 typed ``select`` statements and the session from
``app.database.session``.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base, SoftDeleteMixin

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """CRUD operations for a single ORM model."""

    model: type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── create ──────────────────────────────────────────────────────

    def create(self, **values: Any) -> T:
        obj = self.model(**values)
        self.session.add(obj)
        self.session.flush()
        return obj

    # ── read ────────────────────────────────────────────────────────

    def get(self, id: uuid.UUID | str) -> T | None:
        stmt = select(self.model).where(self.model.id == id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by(self, **filters: Any) -> T | None:
        stmt = select(self.model)
        for key, value in filters.items():
            column = getattr(self.model, key)
            stmt = stmt.where(column == value)
        return self.session.execute(stmt).scalars().first()

    def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
    ) -> list[T]:
        stmt = select(self.model)
        if order_by:
            stmt = stmt.order_by(order_by)
        return list(self.session.execute(stmt.offset(skip).limit(limit)).scalars().all())

    def count(self, **filters: Any) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        return int(self.session.execute(stmt).scalar_one())

    def exists(self, **filters: Any) -> bool:
        return self.get_by(**filters) is not None

    # ── update ──────────────────────────────────────────────────────

    def update(self, obj: T, **values: Any) -> T:
        for key, value in values.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.session.flush()
        return obj

    # ── delete ──────────────────────────────────────────────────────

    def delete(self, obj: T, hard: bool = False) -> None:
        """Soft-delete by default; pass ``hard=True`` for a real delete."""
        if hard or not isinstance(obj, SoftDeleteMixin):
            self.session.delete(obj)
        else:
            obj.soft_delete()
        self.session.flush()

