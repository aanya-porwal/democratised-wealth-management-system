"""Multi-Agent AI Financial Advisor.

This package orchestrates the existing financial engines (never replacing
them) through a tool-driven, provider-independent multi-agent system.

Architecture
------------
* ``providers/``   — LLM provider abstraction (Ollama default; OpenAI,
                     Anthropic, Gemini, Groq, LM Studio as optional plugins;
                     deterministic rule-based fallback with no LLM).
* ``embeddings/``  — local embedding models (sentence-transformers, Ollama,
                     hash fallback).
* ``vectorstore/`` — local vector stores (FAISS, in-memory numpy fallback).
* ``rag/``         — retrieval-augmented generation over a knowledge corpus
                     (SEBI, RBI, Income Tax, mutual-fund education, docs).
* ``memory/``      — PostgreSQL + vector memory (conversation, financial,
                     recommendations, research, preferences, long-term).
* ``tools/``       — the ONLY bridge to financial engines. Tools call the
                     existing services which route through ``EngineAdapter``.
                     The AI never performs calculations.
* ``agents/``      — Planner, Profile, Goal, Portfolio, Research, Scenario,
                     Coach, Memory, Explainability, Critic, Compliance, and
                     Data Validation agents behind a registry.
* ``conversation/``— ConversationManager (history, context, routing, state).
* ``security/``    — prompt-injection guard, output sanitizer, tool policy.
* ``observability/``— agent/tool run logging, latency, model versions.
* ``prompts/``     — versioned YAML prompt templates, separated from code.
"""

from __future__ import annotations

__version__ = "1.0.0"

