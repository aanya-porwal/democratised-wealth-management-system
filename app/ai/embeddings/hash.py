"""Deterministic hash embedding model — zero-dependency fallback.

Creates a fixed-dimension deterministic vector from hashed character
n-grams. Not semantically rich, but always works (no downloads, no
network) and is fully deterministic — ideal for tests and CI.
"""

from __future__ import annotations

import hashlib

import numpy as np

from app.ai.embeddings.base import BaseEmbeddingModel


class HashEmbedding(BaseEmbeddingModel):
    """Character n-gram hashing embeddings (no external deps)."""

    name = "hash"

    def __init__(self, *, model: str | None = None, dimensions: int | None = None) -> None:
        super().__init__(model=model or "hash-ngram-v1", dimensions=dimensions or 384)

    def _load(self) -> None:
        # nothing to load
        self._loaded = True

    def _embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for i, text in enumerate(texts):
            out[i] = self._hash_vector(text)
        return out

    def _hash_vector(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dimensions, dtype=np.float32)
        lower = text.lower()
        # character 2-grams and 3-grams
        grams = self._ngrams(lower, 2) + self._ngrams(lower, 3)
        for gram in grams:
            digest = hashlib.md5(gram.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    @staticmethod
    def _ngrams(text: str, n: int) -> list[str]:
        padded = f"{'#' * (n - 1)}{text}{'$' * (n - 1)}"
        return [padded[i : i + n] for i in range(len(padded) - n + 1)]

