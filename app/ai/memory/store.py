"""Memory store — PostgreSQL + vector memory for the AI layer.

Stores conversation history, financial memories, recommendation history,
research history, user preferences, and long-term context. Uses PostgreSQL
for structured storage and the vector store for semantic retrieval.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.ai.config import ai_settings
from app.ai.embeddings.factory import get_embedding_model
from app.ai.schemas import RetrievedMemory
from app.ai.vectorstore.factory import get_vector_store
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

# Memory type constants
MEMORY_CONVERSATION = "conversation"
MEMORY_FINANCIAL = "financial"
MEMORY_RECOMMENDATION = "recommendation"
MEMORY_RESEARCH = "research"
MEMORY_PREFERENCE = "preference"
MEMORY_LONG_TERM = "long_term"

_MEMORY_TYPES = frozenset({
    MEMORY_CONVERSATION,
    MEMORY_FINANCIAL,
    MEMORY_RECOMMENDATION,
    MEMORY_RESEARCH,
    MEMORY_PREFERENCE,
    MEMORY_LONG_TERM,
})


class MemoryStore:
    """Persistent memory store for the AI layer.

    Uses PostgreSQL (via the existing ORM) for structured storage and
    the vector store for semantic search over memory content.
    """

    def __init__(self) -> None:
        self._embedding = get_embedding_model()
        self._vector_store = get_vector_store()

    # ── write ───────────────────────────────────────────────────────

    def store(
        self,
        user_id: uuid.UUID,
        memory_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        session_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Store a memory row in PostgreSQL and optionally in the vector store."""
        if memory_type not in _MEMORY_TYPES:
            memory_type = MEMORY_CONVERSATION

        record_id = uuid.uuid4()
        meta = dict(metadata or {})
        meta["memory_type"] = memory_type
        meta["user_id"] = str(user_id)
        if session_id:
            meta["session_id"] = str(session_id)

        # Persist to PostgreSQL
        from app.models.ai import AgentMemory

        db = SessionLocal()
        try:
            record = AgentMemory(
                id=record_id,
                user_id=user_id,
                session_id=session_id,
                memory_type=memory_type,
                content=content,
                metadata=meta,
            )
            db.add(record)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("failed to store memory in PostgreSQL: %s", exc)
        finally:
            db.close()

        # Store in vector store for semantic retrieval
        try:
            memory_id = f"memory:{user_id}:{memory_type}:{record_id}"
            vec = self._embedding.embed(content)
            self._vector_store.add(
                [memory_id],
                [content],
                vec,
                [meta],
            )
        except Exception as exc:
            logger.warning("failed to store memory vector: %s", exc)

        return record_id

    # ── retrieve ────────────────────────────────────────────────────

    def retrieve(
        self,
        user_id: uuid.UUID,
        query: str,
        top_k: int | None = None,
        memory_type: str | None = None,
    ) -> list[RetrievedMemory]:
        """Semantically retrieve relevant memories for a user."""
        if not ai_settings.memory_enabled:
            return []
        k = top_k or ai_settings.memory_top_k
        query_vec = self._embedding.embed(query)
        metadata_filter: dict[str, Any] = {"user_id": str(user_id)}
        if memory_type:
            metadata_filter["memory_type"] = memory_type

        chunks = self._vector_store.search(
            query_vec,
            top_k=k,
            metadata_filter=metadata_filter,
            min_score=0.0,
        )
        results: list[RetrievedMemory] = []
        for chunk in chunks:
            mtype = chunk.metadata.get("memory_type", MEMORY_CONVERSATION)
            created_str = chunk.metadata.get("created_at")
            created = None
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str)
                except (ValueError, TypeError):
                    created = None
            results.append(
                RetrievedMemory(
                    id=chunk.id,
                    memory_type=mtype,
                    content=chunk.text,
                    metadata=chunk.metadata,
                    score=chunk.score,
                    created_at=created,
                )
            )
        return results

    # ── conversation history ────────────────────────────────────────

    def get_conversation_history(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve conversation history from PostgreSQL."""
        from app.models.ai import AgentMemory

        db = SessionLocal()
        try:
            records = (
                db.query(AgentMemory)
                .filter(
                    AgentMemory.user_id == user_id,
                    AgentMemory.session_id == session_id,
                    AgentMemory.memory_type == MEMORY_CONVERSATION,
                    AgentMemory.deleted_at.is_(None),
                )
                .order_by(AgentMemory.created_at.asc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": str(r.id),
                    "role": (r.metadata or {}).get("role", "user"),
                    "content": r.content,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        except Exception as exc:
            logger.warning("failed to retrieve conversation history: %s", exc)
            return []
        finally:
            db.close()

    # ── cleanup ─────────────────────────────────────────────────────

    def cleanup_old(self, older_than_days: int = 365) -> int:
        """Soft-delete memories older than ``older_than_days``."""
        from app.models.ai import AgentMemory

        cutoff = datetime.now(timezone.utc)
        from datetime import timedelta

        cutoff -= timedelta(days=older_than_days)
        db = SessionLocal()
        try:
            records = (
                db.query(AgentMemory)
                .filter(AgentMemory.created_at < cutoff, AgentMemory.deleted_at.is_(None))
                .all()
            )
            for r in records:
                r.soft_delete()
            db.commit()
            return len(records)
        except Exception as exc:
            db.rollback()
            logger.warning("memory cleanup failed: %s", exc)
            return 0
        finally:
            db.close()

    def count(self, user_id: uuid.UUID | None = None, memory_type: str | None = None) -> int:
        """Count memories."""
        from app.models.ai import AgentMemory

        db = SessionLocal()
        try:
            q = db.query(AgentMemory).filter(AgentMemory.deleted_at.is_(None))
            if user_id:
                q = q.filter(AgentMemory.user_id == user_id)
            if memory_type:
                q = q.filter(AgentMemory.memory_type == memory_type)
            return q.count()
        finally:
            db.close()
