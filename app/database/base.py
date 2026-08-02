"""SQLAlchemy 2.0 declarative base and shared mixins.

Every ORM table in the application inherits from :class:`Base` and mixes
in:

* :class:`UUIDPrimaryKey` — ``id`` as the canonical UUID primary key.
* :class:`TimestampMixin` — ``created_at`` / ``updated_at`` maintained by
  the database.
* :class:`SoftDeleteMixin` — ``deleted_at`` for soft deletes.

All ``date``/``datetime`` columns are stored timezone-aware (UTC) and
returned timezone-aware.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData, TypeDecorator, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Use a fixed naming convention so Alembic auto-generation produces
# deterministic, reviewable constraint names.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Application declarative base with a naming convention."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def dict(self) -> dict[str, Any]:
        """Convenience: dump all column attributes to a plain dict."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UTCDateTime(TypeDecorator[datetime]):
    """DateTime that always stores and returns timezone-aware (UTC) values."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class UUIDPrimaryKey:
    """UUID primary key mixin (server-generated, non-sequential)."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """``created_at`` / ``updated_at`` maintained by the DB (UTC)."""

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Soft-delete support via a nullable ``deleted_at`` timestamp."""

    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)

    def soft_delete(self) -> None:
        """Mark the row as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Remove the soft-delete marker."""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

