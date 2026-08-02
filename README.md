# Wealth Management System — Backend

A production-ready FastAPI backend for a goal-based financial planning platform.

## Architecture

```
wealth_management_system/
├── app/                     # FastAPI application layer
│   ├── api/routes/          # 14 REST endpoint modules
│   ├── auth/                # JWT + password hashing
│   ├── config/              # Pydantic settings (env-aware)
│   ├── core/                # Cache, exceptions, handlers, logging, security, rate-limit
│   ├── database/            # SQLAlchemy 2.0 engine + session + base models
│   ├── dependencies/        # FastAPI dependency injection
│   ├── middleware/          # Request context middleware
│   ├── models/              # 20 ORM tables (UUID PKs, soft delete)
│   ├── repositories/        # 7 repository classes (CRUD + domain queries)
│   ├── schemas/             # Pydantic v2 request/response schemas
│   ├── services/            # 9 service classes (business logic + engine adapter)
│   ├── tasks/               # Background task wrappers (APScheduler)
│   ├── tests/               # pytest suite (12 test modules)
│   └── utils/               # Pagination helpers
├── engine/                  # Thin re-export shim → financial engine
├── migrations/              # Alembic (initial migration + future)
├── wealth_management_system/ # Financial engine (untouched, pure Python)
├── Dockerfile               # Multi-stage production image
├── docker-compose.yml       # Backend + Postgres + Redis + PgAdmin
└── requirements.txt         # All Python dependencies
```

### Key design decisions

1. **Engine separation** — The financial engine at `wealth_management_system/` is completely independent. The backend calls it as a library via the `engine/` shim. No duplicate calculations exist in the API layer.

2. **Repository pattern** — Every database operation is encapsulated in a repository class. Services never touch the ORM directly.

3. **Service layer** — Service classes orchestrate repositories + the financial engine. They are the only layer that imports from both.

4. **JWT auth with refresh rotation** — Access tokens (30 min) + refresh tokens (7 days, rotated on every use, stored hashed). Redis-backed blacklist for logout.

5. **Soft deletes** — Every table has a `deleted_at` column. Nothing is truly deleted.

## Quick start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (or Docker)
- Redis 7+ (or Docker)

### Local development

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY

# 4. Run database migrations
alembic upgrade head

# 5. Start the API server
uvicorn app.main:app --reload

# 6. Open the docs
# http://localhost:8000/docs
```

### Docker (one command)

```bash
docker compose up --build
```

This starts:
- **Backend** at `http://localhost:8000`
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **PgAdmin** at `http://localhost:5050` (optional, `docker compose --profile tools up`)

## API Endpoints

| Prefix | Description | Auth |
|--------|-------------|------|
| `/api/v1/auth` | Register, login, refresh, logout, password reset | Mixed |
| `/api/v1/users` | User management (admin only) | Admin |
| `/api/v1/profile` | Demographic, financial, behavioral profiles, risk | User |
| `/api/v1/goals` | Goal CRUD, engine analysis, progress snapshots | User |
| `/api/v1/portfolio` | Portfolio CRUD, holdings, value snapshots | User |
| `/api/v1/allocation` | Strategic target allocation (engine) | User |
| `/api/v1/rebalance` | Drift-aware rebalancing (engine) | User |
| `/api/v1/recommendations` | Generate, list, dismiss engine recommendations | User |
| `/api/v1/simulation` | Monte Carlo simulation (engine) | User |
| `/api/v1/scenarios` | What-if scenario analysis (engine) | User |
| `/api/v1/health-score` | 0-100 financial health score (engine) | User |
| `/api/v1/planner` | Full explained financial plan (engine) | User |
| `/api/v1/chat` | Chat sessions (future AI memory) | User |
| `/api/v1/system` | Health, readiness, public info | None |

## Testing

```bash
# Run all backend tests
python -m pytest app/tests -v --tb=short

# Run with coverage
pip install pytest-cov
python -m pytest app/tests --cov=app --cov-report=term-missing

# Run engine tests (legacy, 100+ tests)
python -m pytest wealth_management_system/tests -q
```

## Deployment

### Build the Docker image

```bash
docker build -t wms-backend .
```

### Deploy to Render / Railway / AWS / GCP

1. Set `APP_ENV=production` and a strong `SECRET_KEY` (32+ chars)
2. Point `DATABASE_URL` to a managed PostgreSQL instance
3. Point `REDIS_URL` to a managed Redis instance
4. Run `alembic upgrade head` as a release step
5. Start the server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`

## License

MIT
