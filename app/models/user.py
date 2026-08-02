"""User + role tables."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import (
    UTCDateTime,
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKey,
)


class Role(str, Enum):
    """Role-based access control levels."""

    ADMIN = "admin"
    ADVISOR = "advisor"
    USER = "user"


class User(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """An account that can authenticate and own financial data."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[Role] = mapped_column(
        SAEnum(Role, native_enum=False, length=16),
        default=Role.USER,
        index=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    # relationships
    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    financial_profile: Mapped["FinancialProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    behavioral_profile: Mapped["BehavioralProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

