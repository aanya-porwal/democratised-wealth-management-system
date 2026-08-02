# Production Backend — Implementation TODO

## Milestone: complete the FastAPI + PostgreSQL backend around the financial engine

- [x] Audit existing backend modules and financial engine API surface
- [ ] **A. Fix mismatched modules** (settings, exceptions, audit model/repo, simulation schema/repo/service, health repo/service, recommendation model/repo, planner service)
- [ ] **B. Alembic setup** — alembic.ini, migrations/env.py, script.py.mako, initial migration (PG-compatible, hand-authored from ORM metadata, autogenerate-ready)
- [ ] **C. Routers + app/main.py** — wire middleware, CORS, exception handlers, rate limiting, all routers, /docs metadata
- [ ] **D. app/api/ + app/dependencies/ structural shims**
- [ ] **E. Background tasks** — app/tasks (market data refresh, portfolio snapshot generation, goal progress updates, notification prep) + APScheduler wiring
- [ ] **F. Docker + requirements.txt** — backend deps, Dockerfile, docker-compose.yml (backend, postgres, redis, pgadmin), .env.example
- [ ] **G. Backend pytest suite** — conftest (test DB + client + auth), tests for auth/API/repositories/services/engine integration
- [ ] **H. Docs** — .gitignore update, README.md backend section, TODO completion
- [ ] **I. End-to-end verification** — install deps, run backend tests, run engine tests (100+ green), boot uvicorn

