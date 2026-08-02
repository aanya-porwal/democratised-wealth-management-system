"""System-level tables: settings, market data cache, chat sessions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class SystemSetting(UUIDPrimaryKey, TimestampMixin, Base):
    """Key/value configuration stored in the database (feature flags etc)."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MarketDataCache(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """Cached market data (asset prices, index levels) for offline reads."""

    __tablename__ = "market_data_cache"

    symbol: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    asset_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class ChatSession(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """Future AI-compatibility: a conversational advice session."""

    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="New chat", nullable=False)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True, nullable=False)
    messages: Mapped[dict | None] = mapped_column(JSON, nullable=True)

