# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

**Development** (hot reload via `docker-compose.override.yml`):
```bash
docker compose up
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (Vite dev server)

**Production**:
```bash
docker compose -f docker-compose.yml up
```
- Frontend served by Nginx on port 80, `/api` proxied to backend:8000

**Frontend without Docker** (in `frontend/`):
```bash
npm install
npm run dev       # Vite dev server on :5173
npm run build
```

**Database migrations**:

The backend runs from a built Docker image — `docker compose run --rm backend alembic` does NOT pick up local file changes. Write migration files manually:

```
backend/alembic/versions/<NNNN>_<slug>.py
```

Follow the existing naming convention. Use `down_revision` pointing to the previous migration's `revision` string. Then rebuild the image to apply: `docker compose up --build`.

To check the current head: `docker compose run --rm backend alembic heads`

There is no test suite currently.

## Architecture Overview

**Shoebill Feed** is a self-hosted news aggregator with LLM-powered categorization. The system follows a fetch → deduplicate → LLM-process → score pipeline.

### Services (docker-compose)

| Service | Role |
|---|---|
| `postgres` | Primary store (PostgreSQL 17) |
| `redis` | Celery broker + result backend |
| `backend` | FastAPI REST API on :8000 |
| `celery-worker` | Async task processing (fetch + process queues) |
| `celery-beat` | Cron scheduler; schedule persisted to named volume `celerybeat-data` |
| `frontend` | Nginx serving built React app, proxies `/api` |

### Core Data Flow

1. **Fetch** (every 5 min): `fetch_all_sources()` → individual `fetch_source(source_id)` Celery tasks → fetcher factory (RSS/Reddit/YouTube/IMAP/Scraper) → deduplicated items saved to DB
2. **Process** (every 15 min): `process_unprocessed_items()` → LLM analyzes title+content → writes `abstract`, `category_id`, `relevance_score` (1–10), `impact_score` (1–10) back to `NewsItem`
3. **Cleanup** (daily 3am UTC): deletes non-relevant items older than 30 days

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app; mounts routers under `/api`; slowapi rate-limit middleware on `/api/auth`
- **`config.py`** — All settings loaded from `.env` via Pydantic `Settings`; `jwt_expire_hours` defaults to 24
- **`limiter.py`** — slowapi `Limiter` instance (login: 5/minute)
- **`models/`** — SQLAlchemy models: `NewsItem`, `NewsCluster`, `Source`, `Category`, `CategoryWeight`, `KeywordWeight`, `CategoryKeywordWeight`, `KeywordCluster`, `UserSettings`, `UserTab`
- **`schemas/`** — Pydantic request/response DTOs
- **`api/`** — Route handlers: `news`, `sources`, `categories`, `settings`, `auth`, `clusters`, `tabs`
- **`services/`** — Business logic:
  - `llm/` — Pluggable LLM factory (Anthropic or Ollama); returns structured JSON
  - `fetchers/` — Factory pattern: `RSSFetcher`, `RedditFetcher`, `YouTubeFetcher`, `IMAPFetcher`, `ScraperFetcher`
  - `scoring.py` — Dynamic category/keyword weight computation; `decay_learned_weights` uses bulk SQL (not ORM loops) to avoid `StaleDataError`
  - `deduplication.py` — SHA256 of canonical URL (UTM params stripped) to prevent duplicates
- **`tasks/`** — Celery tasks and Beat schedule; three queues: `fetch`, `process`, `default`

### Frontend (`frontend/src/`)

- **`App.tsx`** — React Router: `/` → `FeedPage`, `/settings` → `SettingsPage`
- **`api/`** — Axios HTTP client and typed endpoint wrappers
- **`stores/`** — Zustand for client state (filter state, active tab)
- **`hooks/`** — TanStack Query hooks for server state; `useInfiniteNews` has `staleTime: 60_000`
- **`components/`** — Organized as `layout/`, `feed/`, `settings/`

### Key Design Decisions

- **Pluggable LLM**: Set `LLM_PROVIDERS=anthropic` or `LLM_PROVIDERS=ollama` in `.env`; comma-separate for ordered fallback, e.g. `LLM_PROVIDERS=ollama,anthropic`. The legacy singular `LLM_PROVIDER` is also accepted. Changing LLM config requires container restart.
- **Dynamic scoring**: `CategoryWeight.weight` grows logarithmically as users mark items as "relevant", influencing the Relevant tab ranking.
- **URL canonicalization**: Tracking parameters are stripped before hashing to prevent duplicate entries for the same article.
- **LLM config is read-only via API**: The settings UI displays current LLM config but all changes require `.env` edits + restart.
- **Non-root container**: Backend/Celery run as UID 1000 (`app` user). Named Docker volumes (e.g. `celerybeat-data`) are pre-created in the Dockerfile so Docker initialises them with the correct ownership. If a volume already exists as root, remove it: `docker volume rm shoebill_feed_celerybeat-data`.
- **PWA updates**: `registerType: "prompt"` — users see a banner when a new version is available and must confirm the reload. Do not change to `autoUpdate`.
- **Virtualizer and React state**: `@tanstack/react-virtual` unmounts components as they scroll off-screen, resetting any local `useState`. All visual state for feed cards (read, relevant, disliked, etc.) must be derived from the TanStack Query cache, never from local component state.
- **ORM loading strategy**: Use `selectinload` for collection relationships (e.g. `NewsCluster.items`, `NewsItem.categories`). Using `joinedload` on a collection causes a cartesian product when items have sub-relationships. `joinedload` is fine for to-one relationships (e.g. `NewsItem.source`).
- **N+1 prevention**: `list_categories` and `list_sources` use a single `GROUP BY` query for counts, not per-row queries. Follow this pattern for any new list endpoint that needs aggregated counts.
- **Auth cookie**: `secure=True`, `httponly=True`, `samesite="strict"`. The `secure` flag is safe behind a Traefik/Nginx TLS proxy because Traefik terminates TLS and forwards over HTTP internally — the browser sets the cookie over HTTPS.

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

```
POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB
LLM_PROVIDERS             # anthropic | ollama | ollama,anthropic (ordered, first = primary)
ANTHROPIC_API_KEY
ANTHROPIC_MODEL           # default: claude-haiku-4-5
OLLAMA_BASE_URL
OLLAMA_MODEL              # default: qwen3:8b
REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET
YOUTUBE_API_KEY
```
