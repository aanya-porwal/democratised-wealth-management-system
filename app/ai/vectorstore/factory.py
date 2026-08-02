"""Vector store registry + factory.

Defaults to FAISS. Falls back to numpy if FAISS is not installed.
"""

from __future__ import annotations

import logging
from typing import Callable

from app.ai.config import AISettings, VectorStoreName
from app.ai.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)

Builder = Callable[[AISettings], BaseVectorStore]

_BUILDERS: dict[VectorStoreName, Builder] = {}


def register_vector_store(name: VectorStoreName, builder: Builder) -> None:
    _BUILDERS[name] = builder


def _default_builders() -> None:
    if _BUILDERS:
        return

    from app.ai.vectorstore.faiss_store import FAISSVectorStore
    from app.ai.vectorstore.numpy_store import NumpyVectorStore

    def _faiss(cfg: AISettings) -> BaseVectorStore:
        return FAISSVectorStore(
            dimensions=cfg.embedding_dimensions,
            index_dir=cfg.vector_index_dir,
        )

    def _numpy(cfg: AISettings) -> BaseVectorStore:
        return NumpyVectorStore(dimensions=cfg.embedding_dimensions)

    register_vector_store(VectorStoreName.FAISS, _faiss)
    register_vector_store(VectorStoreName.NUMPY, _numpy)


def build_vector_store(cfg: AISettings | None = None) -> BaseVectorStore:
    """Build the configured vector store, falling back to numpy."""
    settings = cfg or _current_settings()
    _default_builders()
    builder = _BUILDERS.get(settings.vector_store)
    if builder is None:
        logger.warning(
            "no builder for vector store %s; using numpy fallback",
            settings.vector_store.value,
        )
        return _BUILDERS[VectorStoreName.NUMPY](settings)
    try:
        store = builder(settings)
        # Try to load existing index
        try:
            if store.load(settings.vector_index_dir):
                logger.info("vector store loaded from %s", settings.vector_index_dir)
        except Exception as exc:
            logger.debug("could not load vector store index (%s); starting fresh", exc)
        return store
    except Exception as exc:
        logger.warning(
            "vector store %s failed to build (%s); using numpy fallback",
            settings.vector_store.value,
            exc,
        )
        return _BUILDERS[VectorStoreName.NUMPY](settings)


_vector_store_cache: BaseVectorStore | None = None


def get_vector_store() -> BaseVectorStore:
    global _vector_store_cache
    if _vector_store_cache is None:
        _vector_store_cache = build_vector_store()
    return _vector_store_cache


def reset_vector_store_cache() -> None:
    global _vector_store_cache
    _vector_store_cache = None


def _current_settings() -> AISettings:
    from app.ai.config import ai_settings

    return ai_settings
