# Multi-Agent AI Financial Advisor — Implementation TODO

## Phase 0 — Foundation
- [x] Analyze existing codebase (app/, engine/, wealth_management_system/, security_selection/)
- [x] Plan approved

## Phase 1 — Config + Schemas + Providers
- [x] `app/ai/__init__.py`
- [x] `app/ai/config.py` — AI settings (LLM provider, embeddings, vector store, memory, prompts, tools)
- [x] `app/ai/schemas.py` — typed Pydantic v2 contracts (AgentPlan, ToolRequest, AgentResult, ChatMessage, ...)
- [x] `app/ai/providers/base.py` — `BaseLLMProvider` ABC
- [x] `app/ai/providers/ollama.py` — Ollama (default, free)
- [x] `app/ai/providers/openai.py` — OpenAI (optional plugin)
- [x] `app/ai/providers/anthropic.py` — Anthropic (optional plugin)
- [x] `app/ai/providers/gemini.py` — Gemini (optional plugin)
- [x] `app/ai/providers/groq.py` — Groq (optional plugin)
- [x] `app/ai/providers/lmstudio.py` — LM Studio (optional plugin)
- [x] `app/ai/providers/fallback.py` — deterministic rule-based fallback (no LLM)
- [x] `app/ai/providers/factory.py` — provider registry/factory

## Phase 2 — Embeddings + Vector Store + RAG
- [x] `app/ai/embeddings/base.py` — `BaseEmbeddingModel`
- [x] `app/ai/embeddings/sentence_transformers.py` — sentence-transformers (MiniLM/bge)
- [x] `app/ai/embeddings/ollama.py` — Ollama embeddings
- [x] `app/ai/embeddings/hash.py` — deterministic hash fallback
- [x] `app/ai/embeddings/factory.py`
- [x] `app/ai/vectorstore/base.py` — `BaseVectorStore`
- [x] `app/ai/vectorstore/faiss_store.py` — FAISS (local)
- [x] `app/ai/vectorstore/numpy_store.py` — in-memory numpy fallback
- [x] `app/ai/vectorstore/factory.py`
- [x] `app/ai/rag/knowledge.py` — knowledge corpus (SEBI/RBI/tax/mutual-fund education)
- [x] `app/ai/rag/retriever.py` — RAG retrieval service

## Phase 3 — Memory + Prompts
- [x] `app/ai/memory/store.py` — PostgreSQL + vector memory (conversation, financial, recommendations, research, preferences, long-term)
- [x] `app/ai/prompts/manager.py` — prompt template manager (versioned)
- [x] `app/ai/prompts/templates/*.yaml` — agent prompt templates

## Phase 4 — Tool Execution Layer
- [x] `app/ai/tools/base.py` — `BaseTool` (execute/validate_input/validate_output)
- [x] `app/ai/tools/registry.py` — `ToolRegistry`
- [x] `app/ai/tools/risk_tool.py`, `goal_tool.py`, `allocation_tool.py`, `security_tool.py`, `portfolio_tool.py`, `simulation_tool.py`, `scenario_tool.py`, `research_tool.py`, `database_tool.py`, `market_data_tool.py`, `health_score_tool.py`, `comparison_tool.py`, `profile_tool.py`
- [x] `app/ai/tools/__init__.py`

## Phase 5 — Agents
- [x] `app/ai/agents/base.py` — `BaseAgent`
- [x] `app/ai/agents/registry.py` — `AgentRegistry`
- [x] `app/ai/agents/planner.py` — PlannerAgent
- [x] `app/ai/agents/profile.py` — ProfileAgent
- [x] `app/ai/agents/goal.py` — GoalAgent
- [x] `app/ai/agents/portfolio.py` — PortfolioAgent
- [x] `app/ai/agents/research.py` — ResearchAgent
- [x] `app/ai/agents/scenario.py` — ScenarioAgent
- [x] `app/ai/agents/coach.py` — FinancialCoachAgent
- [x] `app/ai/agents/memory.py` — MemoryAgent
- [x] `app/ai/agents/explainability.py` — ExplainabilityAgent
- [x] `app/ai/agents/critic.py` — CriticAgent
- [x] `app/ai/agents/compliance.py` — ComplianceAgent
- [x] `app/ai/agents/data_validation.py` — DataValidationAgent
- [x] `app/ai/agents/__init__.py`

## Phase 6 — Conversation Manager + Security + Observability
- [x] `app/ai/conversation/manager.py` — ConversationManager
- [x] `app/ai/security/input_guard.py` — PromptInjectionGuard
- [x] `app/ai/security/output_sanitizer.py` — OutputSanitizer
- [x] `app/ai/security/tool_policy.py` — ToolPolicy
- [x] `app/ai/observability/tracker.py` — AgentRunLog tracker
- [x] `app/ai/service.py` — AIOrchestratorService (entry point)

## Phase 7 — Models + Migration
- [x] `app/models/ai.py` — AgentMemory, AgentRunLog, KnowledgeDocument
- [x] `app/models/__init__.py` — register AI models
- [x] `migrations/versions/0002_ai_layer.py` — AI tables

## Phase 8 — API Routes + Wiring
- [x] `app/api/routes/agents.py`
- [x] `app/api/routes/memory.py`
- [x] `app/api/routes/research.py`
- [x] `app/api/routes/scenario.py`
- [x] `app/api/routes/tools.py`
- [x] `app/api/__init__.py` — mount new routers
- [x] `app/main.py` — AI startup (vector store index, scheduler)
- [x] `app/config/settings.py` — AI settings
- [x] `app/tasks/ai.py` — background AI jobs
- [x] `app/api/routes/chat.py` — AI chat + history + session + reset

## Phase 9 — Dependencies + Docs
- [x] `requirements.txt` — AI dependencies (ollama/httpx/faiss-cpu/sentence-transformers/chromadb)
- [x] `README.md` — AI layer docs
- [x] `.env.example` settings (documented in README)

## Phase 10 — Tests
- [x] `app/tests/test_ai_planner.py`
- [x] `app/tests/test_ai_tools.py`
- [x] `app/tests/test_ai_memory.py`
- [x] `app/tests/test_ai_rag.py`
- [x] `app/tests/test_ai_conversation.py`
- [x] `app/tests/test_ai_providers.py`
- [x] `app/tests/test_ai_service.py`

## Phase 11 — Verification
- [ ] `python -m compileall app` — all modules compile
- [ ] `python -m pytest app/tests -v --tb=short` — tests pass

