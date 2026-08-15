# Architecture

## Services

| Service | Role |
|---|---|
| `postgres` | Primary data store (PostgreSQL 17 + pgvector) |
| `redis` | Celery broker and result backend |
| `backend` | FastAPI REST API |
| `celery-worker` | `fetch` and `default` queues, concurrency 4 |
| `celery-worker-process` | `process` queue only, concurrency 1 — deliberately serialized: Ollama runs LLM calls on one GPU, so higher concurrency here just causes queue spikes with no throughput gain |
| `celery-worker-podcast` | `podcast` queue only — script generation (LLM) plus CPU-bound TTS synthesis and ffmpeg encoding for podcast episodes; kept off the `process` queue so it never delays news processing |
| `celery-beat` | Cron scheduler; schedule persisted to a named volume so it survives restarts |
| `frontend` | React app served by Nginx, proxies `/api` to the backend |

An optional `docker-compose.ollama.yml` runs Ollama itself in Docker, on a
shared external network.

## Data flow

1. **Fetch** (`fetch_all_sources`, every 5 minutes): sources with identical
   `(source_type, config)` — e.g. the same public RSS feed added by two
   different users — are fetched once and fanned out to every subscriber,
   so one HTTP request can serve N users. New items are deduplicated by
   canonical-URL hash and content hash, then run through a fast
   title-similarity clustering pass. Clustered items dispatch
   `process_cluster`; standalone items dispatch `process_news_item`.
2. **Process** (LLM analysis, dispatched per-item/cluster above, plus a
   `batch_process_unprocessed` sweep every 15 minutes as a safety net):
   writes `abstract`, categories, extracted keywords, an embedding vector,
   and relevance/impact scores back to the item or cluster. See
   {doc}`llm-providers` for the two-stage/batch/newsletter logic, and
   {doc}`clustering` for the second clustering pass that runs after
   processing.
3. **Batch polling** (every 2 minutes): checks in on any in-flight
   Anthropic Batch API jobs.
4. **Weight decay** (daily): learned category/keyword weights decay
   multiplicatively over time — see {doc}`learning-and-scoring`.
5. **Cleanup** (daily): deletes non-relevant, non-read-later items older
   than 30 days, then removes any clusters left with zero items.
6. **Podcast dispatch** (every 15 minutes): a per-user, timezone-aware
   scheduler checks every active podcast show and dispatches generation
   for any whose local `schedule_time` has just passed and that hasn't
   already produced an episode today. Generation selects the show's top
   stories (reusing the same ranking as the Relevant feed tab, filtered by
   the show's time window), asks the LLM for a multi-host conversational
   script, synthesizes each host's lines with a pluggable TTS provider
   (Piper by default — self-hosted, no cloud service), and assembles the
   result into one MP3 via ffmpeg. A separate daily job deletes episodes
   (and their audio files) older than 30 days.

## Backend layout (`backend/app/`)

- **`main.py`** — FastAPI app; mounts routers under `/api`
- **`config.py`** — all settings, loaded from `.env` (see {doc}`configuration`)
- **`models/`** — SQLAlchemy models
- **`schemas/`** — Pydantic request/response DTOs
- **`api/`** — route handlers (`news`, `sources`, `categories`, `settings`,
  `auth`, `clusters`, `stats`, `tabs`, `push`, `learning`, `tokens`,
  `podcasts`)
- **`services/`**
  - `llm/` — pluggable provider factory + fallback wrapper, plus Anthropic
    Batch API handling and podcast script generation
  - `fetchers/` — one module per source type, registered via a
    `@register_fetcher("type")` decorator (see {doc}`sources`)
  - `clustering.py`, `embedding.py` — see {doc}`clustering`
  - `scoring.py`, `keyword_clustering.py` — see {doc}`learning-and-scoring`
  - `feed_ranking.py` — the Relevant/Impact/Newest ranking used by both
    the feed API and podcast episode selection
  - `deduplication.py` — canonical URL hashing and content hashing
  - `push_service.py` — Web Push notifications
  - `tts/` — pluggable text-to-speech provider factory (`piper_provider.py`
    is the self-hosted default) plus ffmpeg-based audio assembly
  - `podcast_script.py` — episode item selection and LLM script generation
  - `podcast_scheduling.py` — the per-user timezone due-window logic
    behind podcast dispatch
  - `range_streaming.py` — HTTP Range (206 Partial Content) support for
    episode audio playback/seeking
- **`tasks/`** — `celery_app.py` (app + full beat schedule), `fetch_tasks.py`,
  `process_tasks.py`, `podcast_tasks.py`

## Frontend layout (`frontend/src/`)

- **`App.tsx`** — routes: `/login`, `/` (feed), `/podcasts`, `/settings`
- **`api/`** — Axios client + typed endpoint wrappers
- **`stores/`** — Zustand (filter state, theme/locale preferences)
- **`hooks/`** — TanStack Query hooks for server state
- **`components/`** — `layout/`, `feed/`, `settings/`
- **`i18n/`** — 20+ languages via `react-i18next`

## Key design decisions

- **Source dedup + fan-out.** Identical sources across users are fetched
  once per cycle. When a fanned-out item already has LLM results from
  another user's copy of the same URL, those results are reused instead
  of reprocessing — same abstract, keywords, category mapping.
- **Two-stage LLM processing.** A cheap classify-only pass gates an
  expensive abstract-generating pass, so tokens aren't spent summarizing
  articles that don't match any of a user's categories. See {doc}`llm-providers`.
- **Non-root containers.** Backend/Celery run as UID 1000. If a named
  volume (e.g. `celerybeat-data`) already exists owned by root from an
  older setup, remove it: `docker volume rm shoebill_feed_celerybeat-data`.
- **Podcast character vs. voice.** A host's free-text character prompt
  only shapes how the LLM *writes* that host's lines — Piper has no
  emotion/delivery control, so voice timbre is just a mechanically
  assigned speaker. Two hosts sharing a language's only available voice
  will sound identical despite very different character prompts.
- **Per-user timezone scheduling.** Podcast dispatch is the first feature
  needing per-user, timezone-aware timing — every other Beat schedule is a
  fixed global UTC crontab. Beat entries are static, so the per-user
  variability lives in `due_shows()` (a frequent fixed-UTC tick that asks
  "is this show due right now, in its own timezone"), not in Beat config.
