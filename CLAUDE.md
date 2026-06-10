# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

**Development** (hot reload via `docker-compose.override.yml`):
```bash
docker-compose up
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (Vite dev server)

**Production**:
```bash
docker-compose -f docker-compose.yml up
```
- Frontend served by Nginx on port 80, `/api` proxied to backend:8000

**Frontend without Docker** (in `frontend/`):
```bash
npm install
npm run dev       # Vite dev server on :5173
npm run build
```

**Database migrations** (in `backend/`):
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

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
| `celery-beat` | Cron scheduler for periodic tasks |
| `frontend` | Nginx serving built React app, proxies `/api` |

### Core Data Flow

1. **Fetch** (every 5 min): `fetch_all_sources()` → individual `fetch_source(source_id)` Celery tasks → fetcher factory (RSS/Reddit/YouTube/IMAP) → deduplicated items saved to DB
2. **Process** (every 15 min): `process_unprocessed_items()` → LLM analyzes title+content → writes `abstract`, `category_id`, `relevance_score` (1–10), `impact_score` (1–10) back to `NewsItem`
3. **Cleanup** (daily 3am UTC): deletes non-relevant items older than 30 days

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app; mounts routers under `/api`
- **`config.py`** — All settings loaded from `.env` via Pydantic `Settings`
- **`models/`** — SQLAlchemy models: `NewsItem`, `Source`, `Category`, `CategoryWeight`
- **`schemas/`** — Pydantic request/response DTOs
- **`api/`** — Route handlers: `news`, `sources`, `categories`, `settings`
- **`services/`** — Business logic:
  - `llm.py` — Pluggable LLM factory (Anthropic or Ollama); returns structured JSON
  - `fetchers/` — Factory pattern: `RSSFetcher`, `RedditFetcher`, `YouTubeFetcher`, `IMAPFetcher`
  - `scoring.py` — Dynamic category weight computation based on user relevance feedback
  - `deduplication.py` — SHA256 of canonical URL (UTM params stripped) to prevent duplicates
- **`tasks/`** — Celery tasks and Beat schedule; three queues: `fetch`, `process`, `default`

### Frontend (`frontend/src/`)

- **`App.tsx`** — React Router: `/` → `FeedPage`, `/settings` → `SettingsPage`
- **`api/`** — Axios HTTP client and typed endpoint wrappers
- **`stores/`** — Zustand for client state
- **`hooks/`** — TanStack Query hooks for server state
- **`components/`** — Organized as `layout/`, `feed/`, `settings/`

### Key Design Decisions

- **Pluggable LLM**: Set `LLM_PROVIDERS=anthropic` or `LLM_PROVIDERS=ollama` in `.env`; comma-separate for ordered fallback, e.g. `LLM_PROVIDERS=ollama,anthropic`. The legacy singular `LLM_PROVIDER` is also accepted. Changing LLM config requires container restart.
- **Dynamic scoring**: `CategoryWeight.weight` grows logarithmically as users mark items as "relevant", influencing the Relevant tab ranking.
- **URL canonicalization**: Tracking parameters are stripped before hashing to prevent duplicate entries for the same article.
- **LLM config is read-only via API**: The settings UI displays current LLM config but all changes require `.env` edits + restart.

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
