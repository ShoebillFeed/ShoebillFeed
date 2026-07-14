# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

**Development** (hot reload via `docker-compose.override.yml`, auto-loaded by `docker compose up`):
```bash
docker compose up
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (Vite dev server, proxies `/api` to `backend:8000`)

**Production**:
```bash
docker compose -f docker-compose.yml up
```
- Frontend served by Nginx, `/api` proxied to backend:8000. No host port is published by default — put a reverse proxy (Traefik/Nginx) in front, or add a port mapping to the `frontend` service for local testing.

**Frontend without Docker** (in `frontend/`):
```bash
npm install
npm run dev       # Vite dev server on :5173
npm run build     # tsc -b && vite build
```

**Database migrations**:

The backend runs from a built Docker image — `docker compose run --rm backend alembic` does NOT pick up local file changes. Write migration files manually:

```
backend/alembic/versions/<NNNN>_<slug>.py
```

Follow the existing naming convention (`revision` = filename stem). Set `down_revision` to the previous migration's `revision` string. Then rebuild the image to apply: `docker compose up --build`.

To check the current head: `docker compose run --rm backend alembic heads`

There is no test suite currently.

## Architecture Overview

**Shoebill Feed** is a self-hosted, multi-user news aggregator with LLM-powered categorization, clustering, and relevance learning. The system follows a fetch → deduplicate → cluster → LLM-process → score pipeline, all driven by Celery.

### Services (docker-compose)

| Service | Role |
|---|---|
| `postgres` | Primary store (PostgreSQL 17 + pgvector) |
| `redis` | Celery broker + result backend |
| `backend` | FastAPI REST API on :8000 |
| `celery-worker` | `fetch` + `default` queues, concurrency 4 |
| `celery-worker-process` | `process` queue only, concurrency 1 — deliberately serialized because Ollama runs LLM calls on one GPU; higher concurrency here just causes FIFO queue spikes with no throughput gain |
| `celery-beat` | Cron scheduler; schedule persisted to named volume `celerybeat-data` |
| `frontend` | Nginx serving built React app, proxies `/api` |

`docker-compose.ollama.yml` optionally runs Ollama itself in Docker on a shared external network (`shoebill`).

### Core Data Flow

1. **Fetch** (`fetch_all_sources`, every 5 min): groups active sources by `(source_type, config)` fingerprint so identical feeds shared by multiple users are fetched once and fanned out to all subscribers ("companion sources") — one HTTP request serves N users. Dispatches `fetch_source` per group, jittered by `countdown=random.randint(0, 270)` to spread load. New items are deduplicated by URL hash and content hash, then run through `cluster_new_items` (title-Jaccard union-find against items fetched in the last 48h). Items that land in a multi-item cluster dispatch `process_cluster`; standalone items dispatch `process_news_item`.
2. **Process** (`batch_process_unprocessed`, every 15 min, plus per-item dispatch above): LLM analyzes title+content and writes `abstract`, `category_id`(s), `extracted_keywords`, `relevance_score` (1–10), `impact_score` (1–10), plus an embedding vector back to `NewsItem`/`NewsCluster`. See "LLM processing pipeline" below for the two-stage/batch/newsletter logic.
3. **Batch polling** (`poll_llm_batches`, every 2 min): one `_poll_single_batch` task per pending Anthropic batch job so polls run concurrently; cancels and falls back to sync processing if a batch exceeds `LLM_BATCH_MAX_WAIT_MINUTES`.
4. **Keyword cluster refresh** (`refresh_keyword_clusters`, daily 2am UTC): recomputes `KeywordCluster` groupings per user.
5. **Weight decay** (`decay_weights`, daily 4am UTC): multiplicative decay of learned category/keyword weights via bulk SQL (see Key Design Decisions).
6. **Cleanup** (`cleanup_old_items`, daily 3am UTC): deletes non-relevant, non-read-later items older than 30 days, then removes clusters left with zero items.

### LLM processing pipeline (`tasks/process_tasks.py`)

`process_news_item` branches per item:
- **Newsletter emails** (`source.source_type == "email"`): `_expand_newsletter` asks the LLM to extract N individual articles from one email body, replaces the wrapper item with N new `NewsItem`s, dedupes against existing URLs, then re-clusters and dispatches processing for the new items.
- **Short items** (below `UserSettings.llm_min_word_count`, not translating): classify-only via `process_short_item`, no abstract generated — raw content is used as the abstract.
- **Social posts** (`source.source_type == "mastodon"`): `process_item(social_post=True)`; the LLM may return a `generated_title`.
- **Translating** (`UserSettings.output_language` set): always runs full `process_item` so title+abstract get translated, skipping the cost-saving branches.
- **Regular articles**: two-stage — Stage 1 is a cheap classify-only call on the first 600 chars; only if a category matches (or the user has none configured) does Stage 2 run the full-content call that produces the abstract. This avoids paying for abstracts on articles nobody's category set cares about.

`process_cluster` sends all cluster member items to the LLM in one call (deduplicating identical content first via `dedup_cluster_payload` to save tokens) and produces a unified title/abstract/keywords/scores plus a per-item `source_summary`.

`batch_process_unprocessed` prefers the **Anthropic Batch API** when an Anthropic provider is configured (`get_anthropic_provider()`): non-email items are grouped into a batch job (`LLMBatch` model tracks `pending`/`cancelling`/`completed`/`cancelled` status); email/newsletter items always go through the sync per-item path since they mutate the DB (split into multiple items) rather than just annotate it.

**Pluggable LLM providers** (`services/llm/`): `factory.get_llm_provider()` returns a `FallbackProvider` wrapping every provider named in `LLM_PROVIDERS` (comma-separated, ordered — first is primary) — each provider gets 2 attempts with a 5s retry delay before falling through to the next. `factory.get_anthropic_provider()` returns the raw Anthropic instance specifically for Batch API calls; never use `get_llm_provider()` for those. The legacy singular `LLM_PROVIDER` env var is also accepted. Changing LLM config requires a container restart (settings are `lru_cache`d).

### Clustering (`services/clustering.py`)

Two distinct clustering passes:
1. **First pass** (`cluster_new_items`, at fetch time): union-find over title-word Jaccard similarity (`SIMILARITY_THRESHOLD = 0.3`, min 2 shared non-stopword tokens), scoped per-user, comparing new items against each other and against items fetched in the last 48h. New items joining an existing cluster must match the cluster's *combined* title vocabulary (`cluster_anchor_words`), not just one member, to avoid transitive drift into unrelated long-running clusters.
2. **Second pass** (`recluster_processed_item`, after individual LLM processing): for items that stayed standalone, tries pgvector cosine-distance nearest-neighbor search on `NewsItem.embedding` first (`EMBEDDING_DISTANCE_THRESHOLD = 0.18`), falling back to keyword-Jaccard (`KEYWORD_SIMILARITY_THRESHOLD = 0.25`) if no embedding or no match. The keyword path (but not the embedding path — cosine distance already captures holistic similarity) re-checks against the matched cluster's full keyword vocabulary as a drift guard.

Embeddings (`services/embedding.py`) come from Ollama (`nomic-embed-text`, 768-dim, hardcoded — changing the model requires a schema migration) regardless of which provider is configured for text generation; embedding failures are non-fatal and clustering falls back to keywords.

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app; mounts routers under `/api`; slowapi rate-limit middleware on `/api/auth`; creates/repairs the default admin user from `ADMIN_USERNAME`/`ADMIN_PASSWORD` at startup (`_ensure_default_user`)
- **`config.py`** — All settings loaded from `.env` via Pydantic `Settings`, `lru_cache`d
- **`limiter.py`** — slowapi `Limiter` instance (login: 5/minute)
- **`models/`** — SQLAlchemy models: `NewsItem`, `NewsCluster`, `Source`, `Category`, `CategoryWeight`, `KeywordWeight`, `CategoryKeywordWeight`, `KeywordCluster` (+ snapshots), `LLMBatch`, `PushSubscription`, `ApiToken`, `UserSettings`, `UserTab`, `User`
- **`schemas/`** — Pydantic request/response DTOs
- **`api/`** — Route handlers: `news`, `sources`, `categories`, `settings`, `auth`, `clusters`, `stats`, `tabs`, `push`, `learning`, `tokens`
- **`services/`**:
  - `llm/` — Pluggable provider factory + fallback wrapper (see above); `batch_service.py` handles Anthropic Batch API submission/result-application/cross-user propagation
  - `fetchers/` — Registry/factory pattern (`register_fetcher("<type>")` decorator + `get_fetcher`): `RSSFetcher`, `RedditFetcher`, `IMAPFetcher` (newsletters), `MastodonFetcher`, `ScholarFetcher` (registered as `arxiv` — queries arXiv's API directly, not Google Scholar despite the class name), `AtomFetcher`, `LemmyFetcher`, `GitHubFetcher`, `BlueskyFetcher`, `TelegramFetcher`, `ScraperFetcher`. New fetchers register themselves on import — `fetch_tasks.py` imports every fetcher module for its side effect. YouTube and the `scholar` type-name alias were removed (migration `0050_remove_youtube_scholar_types`)
  - `clustering.py` — two-pass clustering, see above
  - `embedding.py` — Ollama embedding generation for semantic clustering
  - `scoring.py` — dynamic category/keyword weight computation; `decay_learned_weights` uses bulk SQL (`UPDATE`/`DELETE`, not ORM loops) to avoid `StaleDataError` under concurrent writes
  - `keyword_clustering.py` — groups related learned keywords into `KeywordCluster`s
  - `deduplication.py` — SHA256 of canonicalized URL (tracking/session/cache-busting params stripped, sorted, fragment dropped) for `url_hash`; separate `content_hash` (first 2000 chars) catches same content re-published under a different URL
  - `push_service.py` — Web Push (VAPID) notifications for high-relevance items/clusters
  - `scraper_assist.py` — helper for the generic `ScraperFetcher`
  - `normalization.py` — keyword normalization shared by clustering/scoring
- **`tasks/`** — `celery_app.py` defines the Celery app + full beat schedule; `fetch_tasks.py` and `process_tasks.py` hold the task implementations described above; three queues: `fetch`, `process`, `default`

### Frontend (`frontend/src/`)

- **`App.tsx`** — React Router: `/login` → `LoginPage`, `/` → `FeedPage`, `/settings` → `SettingsPage`, wrapped in `RequireAuth` (redirects to `/login` only on a real 401 — network/5xx errors show a retry screen instead) and a PWA update banner (`registerType: "prompt"`)
- **`api/`** — Axios HTTP client and typed endpoint wrappers, one file per resource
- **`stores/`** — Zustand: `filterStore` (active tab, category/source filters), `preferencesStore` (theme, etc.)
- **`hooks/`** — TanStack Query hooks for server state; `useInfiniteNews` has `staleTime: 60_000`
- **`components/`** — `layout/`, `feed/`, `settings/`, `icons/`, `ui/`
- **`i18n/`** — `react-i18next` with per-language files (20+ languages: `en`, `de`, `fr`, `es`, `it`, `pt`, `nl`, `pl`, `ru`, `uk`, `zh`, `ja`, `ko`, `tr`, `cs`, `da`, `fi`, `hu`, `nb`, `ro`, `sv`)

### Other components

- **`mcp_server/`** — standalone MCP server (`server.py`) exposing a running Shoebill instance to Claude/MCP clients via its REST API, authenticated with a per-user API token (Settings → Preferences → API Tokens → `ApiToken` model / `api/tokens.py`). Run with `uv run --with mcp --with httpx server.py`; configured via `SHOEBILL_API_URL` / `SHOEBILL_API_TOKEN` env vars. Independent of the Docker Compose stack.

### Key Design Decisions

- **Source dedup + fan-out**: sources with identical `(source_type, config)` across different users are fetched once per cycle (`_config_key` = sha256 of sorted-JSON config) and results fanned out to all subscribing users' `NewsItem` rows — critical for shared public feeds (RSS, subreddits) at multi-user scale. When a fanned-out item already has LLM results from another user's copy (a "donor" item), those results (abstract, keywords, categories, impact score) are reused instead of reprocessing.
- **Pluggable LLM**: `LLM_PROVIDERS=anthropic` or `LLM_PROVIDERS=ollama` in `.env`; comma-separate for ordered fallback, e.g. `LLM_PROVIDERS=ollama,anthropic`. Changing LLM config requires container restart. LLM config is read-only via the settings API — the UI only displays it.
- **Two-stage LLM processing**: cheap classify-only Stage 1 gates an expensive abstract-generating Stage 2, to avoid spending tokens summarizing articles that don't match any of the user's categories.
- **Anthropic Batch API path**: when Anthropic is configured, bulk processing prefers async batch submission over N synchronous calls; `LLMBatch` tracks job status and `poll_llm_batches` dispatches one poll task per pending batch so polling parallelizes; batches that exceed `LLM_BATCH_MAX_WAIT_MINUTES` are cancelled and remaining requests fall back to sync processing.
- **Dynamic scoring**: `CategoryWeight.weight` grows logarithmically as users mark items "relevant" (and is penalized for ignored/unread items via `ignore_penalty_weight`), influencing the Relevant tab ranking; decays daily per-user via `weight_decay_days`.
- **URL + content dedup**: tracking parameters are stripped before hashing to prevent duplicate entries for the same article; a separate content hash catches the same text republished at a different URL.
- **Two-pass clustering**: fast title-Jaccard at fetch time, then a slower embedding/keyword pass after LLM processing catches semantically-related items that didn't share title words.
- **Non-root container**: Backend/Celery run as UID 1000 (`app` user). Named Docker volumes (e.g. `celerybeat-data`) are pre-created in the Dockerfile so Docker initialises them with correct ownership. If a volume already exists as root, remove it: `docker volume rm shoebill_feed_celerybeat-data`.
- **PWA updates**: `registerType: "prompt"` — users see a banner when a new version is available and must confirm the reload. Do not change to `autoUpdate`. The service worker treats `/api/auth/*` as `NetworkOnly` (never cache session state) and other `/api/*` as `NetworkFirst` (serve stale feed if offline).
- **Virtualizer and React state**: `@tanstack/react-virtual` unmounts components as they scroll off-screen, resetting any local `useState`. All visual state for feed cards (read, relevant, disliked, etc.) must be derived from the TanStack Query cache, never from local component state.
- **ORM loading strategy**: use `selectinload` for collection relationships (e.g. `NewsCluster.items`, `NewsItem.categories`). `joinedload` on a collection causes a cartesian product when items have sub-relationships; it's fine for to-one relationships (e.g. `NewsItem.source`).
- **N+1 prevention**: `list_categories` and `list_sources` use a single `GROUP BY` query for counts, not per-row queries. Follow this pattern for any new list endpoint needing aggregated counts.
- **Auth cookie**: `secure=True`, `httponly=True`, `samesite="strict"`. `secure` is safe behind a Traefik/Nginx TLS proxy because the proxy terminates TLS and forwards over HTTP internally — the browser still sets the cookie over HTTPS.

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

```
POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB
LLM_PROVIDERS               # anthropic | ollama | ollama,anthropic (ordered, first = primary)
ANTHROPIC_API_KEY
ANTHROPIC_MODEL              # default: claude-haiku-4-5
OLLAMA_BASE_URL
OLLAMA_MODEL                 # default: qwen3:8b
OLLAMA_EMBEDDING_MODEL        # default: nomic-embed-text (768-dim; changing requires a migration)
OLLAMA_TIMEOUT                # default: 300s
LLM_BATCH_MAX_WAIT_MINUTES     # default: 10
REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USERNAME / REDDIT_PASSWORD
YOUTUBE_API_KEY
JWT_SECRET / JWT_EXPIRE_HOURS  # jwt_expire_hours defaults to 24
ADMIN_USERNAME / ADMIN_PASSWORD
VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY / VAPID_SUBJECT   # web push
```
