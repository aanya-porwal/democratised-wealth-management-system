"""Memory layer — PostgreSQL + vector memory.

Stores conversation history, financial memories, recommendation history,
research history, user preferences, and long-term context. Uses PostgreSQL
for structured storage and the vector store for semantic retrieval.
"""

from __future__ import annotations

from app.ai.memory.store import MemoryStore

__all__ = ["MemoryStore"]
