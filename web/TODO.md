# Wealth Management Frontend — Build Progress

## Phase 1 — Foundation
- [x] Project scaffold (package.json, tsconfig, next.config, postcss)
- [x] Tailwind config + design tokens (dark-first fintech theme)
- [x] Global styles + CSS variables
- [x] lib/utils (cn, formatters, getErrorMessage)
- [x] TypeScript types (mirroring backend Pydantic schemas)

## Phase 2 — Infrastructure
- [x] API client (retries, token refresh, error handling)
- [x] Auth provider + session persistence
- [x] React Query provider
- [x] Theme provider
- [x] API hook modules (goals, portfolio, allocation, health, simulation, recommendations, planner)

## Phase 3 — Design system
- [x] shadcn/ui primitives (button, card, dialog, input, etc.)
- [x] Chart kit (Recharts wrappers)
- [x] Loading skeletons

## Phase 4 — Layout & navigation
- [x] Marketing layout
- [x] App shell (sidebar + topbar)
- [x] Command palette / command center

## Phase 5 — Auth + Onboarding
- [x] Login / Register / Forgot password / Reset pages
- [ ] Conversational onboarding flow

## Phase 6 — Core pages
- [x] Landing
- [x] Dashboard
- [x] Net Worth
- [x] Financial Health
- [x] Goals
- [x] Portfolio
- [x] Asset Allocation

## Phase 7 — Research & analysis pages
- [x] Research Reports
- [x] Security Comparison
- [x] Scenario Analysis
- [x] Monte Carlo
- [x] Recommendations

## Phase 8 — AI + Command Center
- [x] AI Financial Coach (page)
- [x] Financial Command Center workspace

## Phase 9 — Settings, Admin, Advisor
- [x] Settings / Profile / Notification Centre
- [x] Admin panel
- [x] Advisor View

## Phase 10 — Testing & polish
- [x] Vitest + RTL setup (vitest.config.ts, vitest.setup.ts)
- [x] Component tests (metric-card, utils — 12 passing)
- [ ] Integration tests (recommended as follow-up)
- [x] README + env examples

## Status — Verification
- [x] `npx tsc --noEmit` passes cleanly (EXIT_CODE=0)
- [x] `npx next build` succeeds — 24 static pages generated, types valid
- [x] `npx vitest run` — 12/12 tests pass

---

## Phase 11 — AI-First Workspace (approved plan)

### Phase A — AI message architecture
- [x] `types/api.ts` — rich AI types (AiMessageBlock, AiToolCall, AiMemory, AiAction, AiExplainability)
- [x] `lib/ai/parser.ts` — parse ChatResponse into structured message blocks (streaming-ready)
- [x] `lib/ai/context.ts` — per-page AI context builder (contextual AI)
- [x] `lib/api/client.ts` — add aiExecuteTool, aiMemory, aiResearch, aiAgents, aiTools helpers

### Phase B — Persistent AI Assistant panel
- [ ] `components/ai/ai-coach-context.tsx` — open/close + sendMessage + rendering context
- [ ] `components/ai/assistant-panel.tsx` — desktop right panel + mobile bottom sheet (wired into AppShell)
- [ ] `components/ai/ai-message.tsx` — render one rich message (markdown, charts, tables, actions)
- [ ] `components/ai/ai-action-card.tsx` — actionable cards calling backend APIs
- [ ] `components/ai/ai-tool-trace.tsx` — "✓ Portfolio retrieved" tool execution visualization
- [ ] `components/ai/ai-explainability.tsx` — inspect reasoning (data sources, confidence, calculations)
- [ ] Wire into `app-shell.tsx` + `topbar.tsx` (floating Ask AI button + topbar toggle)
- [ ] Refactor `coach/page.tsx` to reuse the shared assistant panel

### Phase C — AI-aware pages + Command Center
- [ ] Rework `app/(app)/page.tsx` — AI-generated daily briefing + action feed
- [ ] `components/ai/ai-page-context-button.tsx` — generic Ask-AI button with per-page context
- [ ] Wire per-page AI context into key pages (dashboard, goals, portfolio, allocation, health, research, compare, monte-carlo, recommendations)

### Phase D — Agentic actions
- [ ] Propose → confirm → execute flows (apply allocation, update goal, accept/decline recommendation, run simulation, schedule review)

### Phase E — Verification & delivery
- [ ] `npx tsc --noEmit` clean
- [ ] `npx next build` succeeds
- [ ] `npx vitest run` passes
- [ ] Update web/README.md
- [ ] Git commit + push `web/` on `blackboxai/multi-agent-ai-advisor` + open PR
