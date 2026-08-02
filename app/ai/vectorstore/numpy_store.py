"""In-memory numpy vector store — zero-dependency fallback.

Simple brute-force cosine search over a list of numpy arrays. No disk
persistence, no external dependencies. Used as a fallback when FAISS is
not available.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from app.ai.vectorstore.base import (
    BaseVectorStore,
    ScoredChunk,
    VectorStoreError,
)

logger = logging.getLogger(__name__)


class NumpyVectorStore(BaseVectorStore):
    """Brute-force cosine similarity via numpy."""

    name = "numpy"

    def __init__(self, *, dimensions: int = 384) -> None:
        super().__init__(dimensions=dimensions)
        self._vectors: list[np.ndarray] = []
        self._ids: list[str] = []
        self._metadatas: dict[str, dict[str, Any]] = {}

    # ── BaseVectorStore ────────────────────────────────────────────

    def _add(
        self,
        ids: list[str],
        texts: list[str],
        vectors: np.ndarray,
        metadatas: list[dict[str, Any]],
    ) -> int:
        for i, cid in enumerate(ids):
            meta = dict(metadatas[i]) if i < len(metadatas) else {}
            meta["text"] = texts[i]
            self._ids.append(cid)
            self._vectors.append(vectors[i].copy())
            self._metadatas[cid] = meta
        return len(ids)

    def _search(
        self,
        query_vector: np.ndarray,
        *,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
        min_score: float,
    ) -> list[ScoredChunk]:
        if not self._vectors:
            return []
        q = query_vector.ravel().astype(np.float32)
        q_norm = float(np.linalg.norm(q))
        if q_norm > 0:
            q = q / q_norm
        scored: list[tuple[float, int]] = []
        for idx, vec in enumerate(self._vectors):
            v = vec.ravel().astype(np.float32)
            v_norm = float(np.linalg.norm(v))
            if v_norm > 0:
                v = v / v_norm
            score = float(np.dot(q, v))
            cid = self._ids[idx]
            meta = self._metadatas.get(cid, {})
            if metadata_filter and not _matches_filter(meta, metadata_filter):
                continue
            if score < min_score:
                continue
            scored.append((score, idx))
        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[ScoredChunk] = []
        for score, idx in scored[:top_k]:
            cid = self._ids[idx]
            meta = self._metadatas.get(cid, {})
            results.append(
                ScoredChunk(
                    id=cid,
                    text=meta.get("text", ""),
                    score=float(score),
                    metadata={k: v for k, v in meta.items() if k != "text"},
                )
            )
        return results

    def delete(self, ids: list[str]) -> int:
        remove = set(ids)
        keep_idx = [i for i, cid in enumerate(self._ids) if cid not in remove]
        removed = len(self._ids) - len(keep_idx)
        self._ids = [self._ids[i] for i in keep_idx]
        self._vectors = [self._vectors[i] for i in keep_idx]
        self._metadatas = {cid: self._metadatas[cid] for cid in self._ids}
        return removed

    def count(self) -> int:
        return len(self._ids)

    def clear(self) -> None:
        self._vectors = []
        self._ids = []
        self._metadatas = {}

    def save(self, path: str) -> None:
        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        data = {
            "ids": self._ids,
            "metadatas": self._metadatas,
            "vectors": [v.tolist() for v in self._vectors],
        }
        (target / "numpy_store.json").write_text(json.dumps(data, default=str), encoding="utf-8")

    def load(self, path: str) -> bool:
        target = Path(path) / "numpy_store.json"
        if not target.exists():
            return False
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            self._ids = list(data.get("ids", []))
            self._metadatas = {k: dict(v) for k, v in data.get("metadatas", {}).items()}
            self._vectors = [np.asarray(v, dtype=np.float32) for v in data.get("vectors", [])]
            return True
        except Exception as exc:
            logger.warning("failed to load numpy store: %s", exc)
            return False


def _matches_filter(meta: dict[str, Any], filt: dict[str, Any]) -> bool:
    for key, expected in filt.items():
        if meta.get(key) != expected:
            return False
    return True
