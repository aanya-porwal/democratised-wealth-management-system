"""AI/ML models — agent run logs, memory, knowledge base."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey, UTCDateTime


class AgentRunLog(UUIDPrimaryKey, TimestampMixin, Base):
    """Observability log for agent runs."""

    __tablename__ = "agent_run_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    agent: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_names: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)


class UserMemory(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """Conversation, financial, and preference memory."""

    __tablename__ = "user_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    memory_type: Mapped[str] = mapped_column(
        String(32), default="conversation", nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class KnowledgeDocument(UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, Base):
    """RAG knowledge base documents."""

    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="manual", nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general", nullable=False, index=True)
    embedding: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    version: Mapped[str | None] = mapped_column(String(16), nullable=True)
