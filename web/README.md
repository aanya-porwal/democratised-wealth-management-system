# Wealth Management Web

Production-grade Next.js (App Router) frontend for the Wealth Management
System. It consumes the FastAPI backend exclusively — **no business logic
lives in the frontend.**

## Stack

- **Next.js 14 (App Router)** + React 18 + TypeScript
- **TailwindCSS** + shadcn/ui primitives
- **TanStack Query** (server state)
- **React Hook Form** + Zod (forms)
- **Recharts** (charts) + **Framer Motion** (motion)
- **Vitest** + Testing Library (tests)

## Getting started

```bash
cd capstone/wealth-management-system/web
npm install
npm run dev        # http://localhost:3000
```

The backend must be running at `http://localhost:8000`. Requests are
proxied via Next rewrites (`/api/v1/*` → `NEXT_PUBLIC_API_URL`).

### Environment

| Variable                  | Default                | Purpose                    |
| ------------------------- | ---------------------- | -------------------------- |
| `NEXT_PUBLIC_API_URL`     | `http://localhost:8000` | Backend base URL          |

Copy `.env.example` to `.env.local` and adjust as needed.

## Scripts

```bash
npm run dev         # start dev server
npm run build       # production build (type-checks)
npm run start       # serve production build
npm run typecheck   # tsc --noEmit
npm run lint        # eslint
npm run test        # vitest run
npm run test:watch  # vitest watch
```

## Architecture

```
app/
  page.tsx                 # Landing page
  (auth-ish)/login, register, forgot-password
  (app)/                   # authenticated shell (sidebar + topbar)
    page.tsx               # Financial Command Center
    dashboard, goals, net-worth, health, portfolio, allocation
    coach, research, compare, scenarios, monte-carlo, recommendations
    notifications, profile, settings, advisor, admin
components/
  layout/                  # app-shell, sidebar, topbar
  ui/                      # shadcn-style primitives
  charts/                  # Recharts wrappers
  providers/               # auth, query, theme
  metric-card.tsx, page-placeholder.tsx, skeletons.tsx ...
hooks/                     # React Query hooks per domain
lib/
  api/client.ts            # typed fetch client (retries, token refresh)
  utils.ts                 # formatters + cn + error helpers
types/
  api.ts                   # mirror of backend Pydantic schemas
```

### API client

`lib/api/client.ts` is a fully typed fetch wrapper that:

- attaches the JWT `Authorization` header automatically
- performs single-flight token refresh on 401 + retries with backoff
- survives a 7-day rotated refresh token
- normalises API errors into a typed `ApiError`

### Server state

Each domain exposes a small React Query hook module (`hooks/use-*.ts`).
Queries default to 60s stale time with 2 retries; mutations invalidate the
relevant query keys so the UI stays consistent.

## Pages

- **Command Center** — unified real-time workspace (portfolio, goals, AI coach,
  research, market watch, notifications, tasks)
- **Dashboard** — net worth, health score, goals, allocation, performance,
  today's insights
- **Goals** — create/edit/delete/prioritise/track goals with progress bars
- **Portfolio / Allocation** — holdings, asset mix, target allocation, rebalance
- **Health** — 0–100 financial health score with factor breakdown
- **Research / Compare** — institutional-style research reports and side-by-side
  security comparisons
- **Scenarios / Monte Carlo** — what-if analysis and 10,000-run simulations
  with fan charts
- **Coach** — persistent AI financial advisor (markdown, suggested follow-ups)
- **Advisor / Admin** — advisor client dashboard and admin management
- **Settings / Profile / Notifications** — account management centre

## Testing

```bash
npm run test
```

Component tests use Vitest + Testing Library with jsdom. Tests cover the
UI primitives and utility helpers; integration coverage can be added by
mocking `lib/api/client`.

## Notes

- All computations are delegated to the backend (`/api/v1`).
- JWT access token (30 min) + refresh token (7 days, rotated on refresh).
- Light/dark/system theming via `next-themes` (dark first).

