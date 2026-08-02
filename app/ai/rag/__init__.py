"""Retrieval-Augmented Generation (RAG) layer.

Indexes a knowledge corpus (SEBI, RBI, Income Tax, mutual fund education,
product documentation, internal research reports) and provides retrieval
for the AI agents. Uses the local embedding model + vector store.
"""

from __future__ import annotations

from app.ai.rag.knowledge import KnowledgeCorpus, KnowledgeDocument
from app.ai.rag.retriever import RAGRetriever

__all__ = ["KnowledgeCorpus", "KnowledgeDocument", "RAGRetriever"]
