"""Base vector store contract."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

import numpy as np

from app.ai.embeddings.base import BaseEmbeddingModel


class VectorStoreError(Exception):
    """Base error for vector-store failures."""


@dataclass(frozen=True)
class VectorChunk:
    """A chunk of text with its metadata and embedding vector."""

    id: str
    text: str
    vector: np.ndarray  # shape (dimensions,)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ScoredChunk:
    """A retrieved chunk with a similarity score."""

    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseVectorStore(ABC):
    """Provider-agnostic approximate-nearest-neighbour interface.

    Implementations store chunks with embeddings and support cosine
    similarity retrieval. FAISS and an in-memory numpy store are provided.
    """

    name: str = "base"

    def __init__(self, *, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def add(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        vectors: np.ndarray,
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> int:
        """Add (or replace) chunks identified by ``ids``."""
        if len(ids) != len(texts):
            raise VectorStoreError("ids and texts must have equal length")
        if vectors.shape[0] != len(ids):
            raise VectorStoreError("vectors row count must match ids length")
        if vectors.shape[1] != self.dimensions:
            raise VectorStoreError(
                f"vector dimension {vectors.shape[1]} != store dimension {self.dimensions}"
            )
        metas = [dict(m or {}) for m in (metadatas or [])] if metadatas else [{} for _ in ids]
        return self._add(ids, texts, vectors.astype(np.float32), metas)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        *,
        metadata_filter: dict[str, Any] | None = None,
        min_score: float = 0.0,
    ) -> list[ScoredChunk]:
        """Return the ``top_k`` most similar chunks to ``query_vector``."""
        start = time.perf_counter()
        results = self._search(
            query_vector.astype(np.float32).ravel(),
            top_k=top_k,
            metadata_filter=metadata_filter,
            min_score=min_score,
        )
        # tiny guard for total time; latency measured by callers
        return results

    @abstractmethod
    def _add(
        self,
        ids: list[str],
        texts: list[str],
        vectors: np.ndarray,
        metadatas: list[dict[str, Any]],
    ) -> int:
        """Implementation of add."""

    @abstractmethod
    def _search(
        self,
        query_vector: np.ndarray,
        *,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
        min_score: float,
    ) -> list[ScoredChunk]:
        """Implementation of search."""

    @abstractmethod
    def delete(self, ids: Sequence[str]) -> int:
        """Remove chunks by id."""

    @abstractmethod
    def count(self) -> int:
        """Total number of chunks in the store."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all chunks."""

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist the index to disk (if supported)."""

    @abstractmethod
    def load(self, path: str) -> bool:
        """Load the index from disk. Returns False if absent."""

    def close(self) -> None:  # pragma: no cover - optional
        pass

