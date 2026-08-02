"""Background AI tasks — memory cleanup, embedding updates, knowledge indexing, cache refresh."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.ai.config import ai_settings
from app.ai.rag.knowledge import KnowledgeCorpus
from app.ai.rag.retriever import RAGRetriever
from app.core.logging import get_logger
from app.database.session import session_scope

logger = get_logger(__name__)


def cleanup_old_memories() -> None:
    """Soft-delete memories older than the retention period."""
    if not ai_settings.memory_enabled:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=ai_settings.memory_retention_days)
    from app.models.ai import UserMemory
    with session_scope() as session:
        old = (
            session.query(UserMemory)
            .filter(UserMemory.created_at < cutoff, UserMemory.deleted_at.is_(None))
            .all()
        )
        for record in old:
            record.soft_delete()
        logger.info("Marked %d old memories for cleanup", len(old))


def index_knowledge_base() -> None:
    """Index knowledge documents into the vector store."""
    if not ai_settings.rag_enabled:
        return
    try:
        corpus = KnowledgeCorpus()
        retriever = RAGRetriever()
        docs = corpus.get_all_documents()
        for doc in docs:
            retriever.add_document(doc)
        logger.info("Indexed %d knowledge documents", len(docs))
    except Exception as exc:
        logger.warning("Knowledge indexing failed: %s", exc)


def refresh_embeddings() -> None:
    """Refresh embeddings for existing memories and documents."""
    if not ai_settings.rag_enabled:
        return
    try:
        from app.ai.embeddings.factory import get_embedding_model
        from app.ai.vectorstore.factory import get_vector_store
        model = get_embedding_model()
        store = get_vector_store()
        store.refresh_embeddings(model)
        logger.info("Embeddings refresh completed")
    except Exception as exc:
        logger.warning("Embeddings refresh failed: %s", exc)


def rebuild_search_index() -> None:
    """Rebuild the full-text / vector search index."""
    if not ai_settings.rag_enabled:
        return
    try:
        index_knowledge_base()
        logger.info("Search index rebuilt")
    except Exception as exc:
        logger.warning("Search index rebuild failed: %s", exc)
