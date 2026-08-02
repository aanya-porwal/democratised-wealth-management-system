"""Embedding model registry + factory.

Selects the embedding model from configuration. If the configured model
cannot be built (e.g. sentence-transformers not installed), the hash
fallback is used so RAG/memory never crash.
"""

from __future__ import annotations

import logging
from typing import Callable

from app.ai.config import AISettings, EmbeddingProviderName
from app.ai.embeddings.base import BaseEmbeddingModel

logger = logging.getLogger(__name__)

Builder = Callable[[AISettings], BaseEmbeddingModel]

_BUILDERS: dict[EmbeddingProviderName, Builder] = {}


def register_embedding(name: EmbeddingProviderName, builder: Builder) -> None:
    _BUILDERS[name] = builder


def _default_builders() -> None:
    if _BUILDERS:
        return

    from app.ai.embeddings.hash import HashEmbedding
    from app.ai.embeddings.ollama import OllamaEmbedding
    from app.ai.embeddings.sentence_transformers import SentenceTransformerEmbedding

    def _sentence_transformers(cfg: AISettings) -> BaseEmbeddingModel:
        return SentenceTransformerEmbedding(
            model=cfg.embedding_model, dimensions=cfg.embedding_dimensions
        )

    def _ollama(cfg: AISettings) -> BaseEmbeddingModel:
        return OllamaEmbedding(
            model=cfg.embedding_model,
            dimensions=cfg.embedding_dimensions,
            base_url=cfg.llm_base_url,
        )

    def _hash(cfg: AISettings) -> BaseEmbeddingModel:
        return HashEmbedding(dimensions=cfg.embedding_dimensions)

    register_embedding(EmbeddingProviderName.SENTENCE_TRANSFORMERS, _sentence_transformers)
    register_embedding(EmbeddingProviderName.OLLAMA, _ollama)
    register_embedding(EmbeddingProviderName.HASH, _hash)


def build_embedding_model(cfg: AISettings | None = None) -> BaseEmbeddingModel:
    """Build the configured embedding model, falling back to hash."""
    settings = cfg or _current_settings()
    _default_builders()
    builder = _BUILDERS.get(settings.embedding_provider)
    if builder is None:
        logger.warning(
            "no builder for embedding %s; using hash fallback", settings.embedding_provider.value
        )
        return _BUILDERS[EmbeddingProviderName.HASH](settings)
    try:
        return builder(settings)
    except Exception as exc:
        logger.warning(
            "embedding %s failed to build (%s); using hash fallback",
            settings.embedding_provider.value,
            exc,
        )
        return _BUILDERS[EmbeddingProviderName.HASH](settings)


_embedding_cache: BaseEmbeddingModel | None = None


def get_embedding_model() -> BaseEmbeddingModel:
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = build_embedding_model()
    return _embedding_cache


def reset_embedding_cache() -> None:
    global _embedding_cache
    _embedding_cache = None


def _current_settings() -> AISettings:
    from app.ai.config import ai_settings

    return ai_settings

