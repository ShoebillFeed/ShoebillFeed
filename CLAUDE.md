# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

**Development** (hot reload via `docker-compose.override.yml`, auto-loaded by `docker compose up`):
```bash
docker compose up
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (Vite dev server, proxies `/api` to `backend:8000`)
- Behind a reverse proxy on a real domain (e.g. testing on a server before merge): Vite 6 rejects any request whose `Host` header isn't `localhost`/`127.0.0.1` by default, surfacing as a `403 Blocked request` for every single request regardless of path/method. Set `VITE_ALLOWED_HOSTS` (comma-separated) in `.env` — `docker-compose.override.yml` passes it to the `frontend` service automatically. See `docs/development.md` (`allowedHosts` in `frontend/vite.config.ts`). Doesn't affect production (Nginx serves prebuilt static files, no dev-server host check).

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

**Tests**: `backend/tests/` (pytest, run against a real Postgres+pgvector instance — see `.github/workflows/backend-tests.yml`) and `frontend/src/**/*.test.{ts,tsx}` (Vitest, `npm test`). Both run in CI on every push/PR touching their respective directory. The backend suite uses a `db_session` fixture (SAVEPOINT-scoped, rolled back per test) and an `auth_client` fixture for authenticated `TestClient` requests — see `backend/tests/conftest.py`. Frontend tests are narrow in scope by convention: pure functions/stores and fully self-contained presentational components only — nothing here mocks network or TanStack Query state.

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
| `celery-worker-podcast` | `podcast` queue only — podcast script generation (LLM) + CPU-bound TTS synthesis + ffmpeg encoding; kept off `process` so it never delays news processing |
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
7. **Podcast dispatch** (`dispatch_due_podcasts`, every 15 min): per-user, timezone-aware — see "Podcast pipeline" below. **Podcast episode cleanup** (`cleanup_old_podcast_episodes`, daily 3:30am UTC): deletes episodes (and their audio files on disk) older than 30 days.

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

### Podcast pipeline (`tasks/podcast_tasks.py`, `services/podcast_*.py`, `services/tts/`)

A `PodcastShow` is a saved config (up to 3 hosts, an optional free-text `description` concept, category/source filters, time window, target length ≤15 min, language, `speech_rate`, daily `schedule_time` + IANA `timezone`); each run produces a `PodcastEpisode` (status `pending`/`generating`/`ready`/`failed`).

- **Scheduling** (`services/podcast_scheduling.py::due_shows`): the *first* per-user, timezone-aware schedule in this codebase — every other Beat entry is a fixed global UTC crontab. Beat itself stays static (`dispatch_due_podcasts` ticks every 15 min); `due_shows(db, now_utc)` converts each active show's local `schedule_time` via `zoneinfo.ZoneInfo(show.timezone)` and checks whether local-now falls in `[scheduled_today, scheduled_today + 15min)`. Idempotency (no double-dispatch across overlapping ticks) is a plain "does an episode already exist with `created_at >= scheduled_today_utc`" check — good enough since there's exactly one `celery-beat` process; not a distributed lock.
- **Item selection** (`services/podcast_script.py::select_episode_items`): reuses `services/feed_ranking.py::build_feed(tab="relevant", ...)` — the exact same personalized ranking as the feed's Relevant tab — filtered further by the show's `category_ids`/`source_ids`, then by `time_window_hours`, then capped by `estimate_story_count(target_length_minutes, host_count)` (a word-budget heuristic driven by `llm.base.PODCAST_WORDS_PER_MINUTE` — measured directly from real Piper output pace via an end-to-end test, not a natural-speech textbook figure — capped at 15 stories). This is a pre-generation bound, not a post-hoc truncation — the LLM is told the target length and paces itself.
- **Script generation**: `build_script()` calls `LLMProvider.generate_podcast_script(hosts, stories, target_minutes, language, show_description)` — a concrete (non-abstract) method on the `LLMProvider` base class (same pattern as `process_short_item`/`generate_category_prompt`), so it's free on `FallbackProvider` too. `show_description` (the show's free-text concept, e.g. "focus on market impact, skeptical tone") is injected into the system prompt on top of each host's own `character_prompt` — the former shapes *what* gets covered and the overall angle, the latter shapes *how each host* talks. The prompt states an explicit target word count (`target_minutes * PODCAST_WORDS_PER_MINUTE`, plus a derived words-per-story figure) rather than leaving the model to compute "minutes × pace" itself — real end-to-end testing showed models (especially smaller local ones) adhere far more closely to a stated number than to an indirect rate framing, though they still tend to undershoot it, more so for weaker models. Follows the existing structured-output convention exactly: `PODCAST_SCRIPT_SYSTEM_PROMPT` + `parse_podcast_script_response()` (fence-strip → `json.loads` → `json_repair.repair_json` fallback, same as every other `parse_*_response`). Produces a list of `{host_id, story_index, text}` turns — a scripted *dialogue* across all hosts, not independent per-host segments; `story_index` (nullable, for welcome/sign-off/banter) ties a turn back to the "Story N" it's discussing, which is what makes shownote bookmarks possible (see below). The output token budget (`podcast_script_max_tokens()`) scales with `target_minutes` rather than a fixed constant — a fixed 4096-token cap silently truncated longer episodes, since `json_repair` closes the cut-off JSON instead of erroring, so the resulting audio ended up a fraction of the configured length with no visible error. On the Ollama path specifically, `OllamaProvider` also sizes `num_ctx` per-request (`_num_ctx_for()`, estimated from prompt + requested output length) — Ollama does not grow its context window to fit the prompt automatically, so a large podcast-script prompt against a model's small default context previously came back truncated or empty instead of erroring.
- **TTS** (`services/tts/`): pluggable provider behind `TTSProvider` (2 abstract methods: `list_voices`, `synthesize(text, voice_id, out_path, speech_rate=1.0)`; `pick_distinct_voices` is concrete on the base class and handles graceful degradation — cycles through available voices if a language has fewer than the host count). Two implementations:
  - `piper_provider.py` — the default: Piper (self-hosted, CPU/ONNX, GPL-3.0 — compatible with this project's AGPLv3) running **in-process**, via the `piper-tts` PyPI package's `PiperVoice.load()` / `voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(speaker_id=..., length_scale=...))` API. `speech_rate` is listener-facing (1.0 = normal, > 1.0 = faster, range 0.75–1.5) and inverted at the call site into Piper's `length_scale` (`< 1` = faster) — `1.0 / speech_rate`. `piper_voices.py` is a static language → Piper-model catalog (`PIPER_VOICE_CATALOG`); languages with no known Piper voice return `[]` from `list_voices()` rather than silently substituting the wrong language. Voice `.onnx`/`.onnx.json` files are lazily downloaded from Hugging Face into the `piper-voices` volume on first use, cached per-process thereafter.
  - `network_provider.py` (`NetworkTTSProvider`, `TTS_PROVIDER=network`) — an HTTP client for the standalone **`tts_service/`** container (see below), the same shape as `OllamaProvider` talking to a standalone Ollama instance. `synthesize()` POSTs `{text, voice_id, speech_rate}` to `/synthesize` and writes the raw `audio/wav` response body to `out_path`; duration comes from the response's `X-Duration-Seconds` header (the service already computed it during synthesis, so the client doesn't re-parse the WAV). `list_voices()` GETs `/voices?language=`. Requires `TTS_SERVICE_URL`; `get_tts_provider()` raises at construction time if it's unset. Lets synthesis run on different hardware (e.g. a GPU machine) than the Celery worker.
  - **Important tradeoff**: a host's `character_prompt` only shapes how the *script* is written (tone, vocabulary, personality), not delivery/emotion — voice timbre is just a mechanically assigned speaker for both engines below. Two hosts sharing a language's only available voice sound identical despite different character prompts. Surfaced directly in the settings form's copy, not hidden. Applies equally whether the engine runs in-process or via `tts_service/` — it's an engine limitation, not a deployment one.

### `tts_service/` — standalone TTS container

A fourth, independently-built/deployed project (like `frontend/`/`backend`/`mcp_server/` are from each other — no shared code across that boundary; `piper_voices.py` is duplicated by hand between here and `backend/app/services/tts/`, not imported). Exists so podcast synthesis can be offloaded to different hardware than the main stack, mirroring exactly how `docker-compose.ollama.yml` lets Ollama run standalone for LLM calls — `NetworkTTSProvider` above is the client side of this.

- **Structure**: `app/main.py` (FastAPI: `GET /health`, `GET /voices?language=`, `POST /synthesize`) → `app/engines/factory.py::get_engine()` (picks an engine by `TTS_ENGINE` env var, `lru_cache`d, mirrors `backend/app/services/tts/factory.py`) → a `TTSEngine` implementation (`app/engines/base.py` is the abstract interface: `list_voices`/`synthesize(text, voice_id, speech_rate) -> (wav_bytes, duration_seconds)`, deliberately returning bytes rather than writing a file since this runs as a stateless HTTP service). Two engines, both always installed in the image regardless of `TTS_ENGINE` — switching is a runtime env var, no rebuild needed (unless also changing `TTS_GPU`):
  - `piper_engine.py` (`TTS_ENGINE=piper`, default) — a near-verbatim port of `backend/app/services/tts/piper_provider.py`.
  - `kokoro_engine.py` (`TTS_ENGINE=kokoro`) — wraps the `kokoro` PyPI package (Apache 2.0; `hexgrad/Kokoro-82M`, a small torch model, distinct in character/quality from Piper, not just a re-skin). One `KPipeline` per Kokoro `lang_code`, lazily constructed and cached (`_get_pipeline`); `kokoro_voices.py` maps Shoebill's language codes to Kokoro's own `lang_code` + curated voice-name lists (`af_heart`, `bm_daniel`, etc. — named voices, not numbered speakers like Piper's English model). Only English (American) plus the espeak-backed languages (es/fr/it/pt) are catalogued — Chinese/Japanese would need their own `misaki[zh]`/`misaki[ja]` extras and are left out for now. `speed` is passed straight through with **no inversion** (unlike Piper's `length_scale`) — Kokoro's own duration formula divides by `speed`, so higher is already faster, matching Shoebill's `speech_rate` convention directly. Two build/runtime snags real end-to-end testing caught, both fixed in the `Dockerfile`, neither obvious from the library's own docs: (1) `huggingface_hub` (used for the base model + voice pack downloads) defaults its cache to `$HOME`, which doesn't exist for the non-root `app` user — fixed via `ENV HF_HOME=/data/voices/hf-cache`, which also means downloads persist across restarts the same way Piper's do; (2) `misaki`'s English G2P (`misaki.en.G2P`) needs the `en_core_web_sm` spaCy model and otherwise tries to `pip install` it at *request time* on first use, which fails as non-root even before considering that a request handler shouldn't be doing network installs — fixed by pre-installing it at build time (`RUN python -m spacy download en_core_web_sm`, as root, before the `USER app` switch).
- **GPU is a two-layer, independently optional knob**, per its own explicit request that this not be forced on: **build-time** — `Dockerfile`'s `TTS_GPU` build arg controls whether GPU-capable builds of *both* ML backends get installed (`onnxruntime-gpu` over the CPU-only `onnxruntime` that `piper-tts` pulls in by default; `torch`'s CUDA-bundled default build over the CPU-only wheel installed first from `download.pytorch.org/whl/cpu`) — both installed second with `--force-reinstall` to win over what's already there. **Run-time** — `TTS_DEVICE=cpu|cuda` controls whether `PiperEngine`/`KokoroEngine` pass `use_cuda=True`/`device="cuda"` into their respective library's own API (real parameters on both, not bolted on here). Both default to CPU/off; a plain `docker compose -f docker-compose.tts.yml up -d --build` needs no GPU hardware or drivers at all.
- **Deployment**: `docker-compose.tts.yml` (repo root, standalone — not part of `docker-compose.yml`) has its own named volume for downloaded voice models (`tts_voices`, separate from the main stack's `piper-voices` — they're different machines) and a commented-out NVIDIA `deploy.resources.reservations.devices` block, same convention as `docker-compose.ollama.yml`.
- **Audio assembly** (`services/tts/audio_assembly.py`): per-turn WAVs are concatenated (with a short silence gap, `SILENCE_GAP_SECONDS`, between turns) and encoded to one MP3 via an `ffmpeg` subprocess (`concat` demuxer + `libmp3lame`), not `pydub` — ffmpeg is needed for compression anyway, so no reason to add a second dependency for concatenation. `SILENCE_GAP_SECONDS` is also reused by `podcast_script.py::build_episode_records` to compute shownote bookmark timestamps, so the two stay in lockstep with what's actually assembled.
- **Generation task** (`generate_podcast_episode`, queue `podcast`): creates the episode row as `generating` immediately, then select→script→synthesize→assemble; any exception anywhere in that chain is caught and sets `status="failed"` + `error_message` — the episode never gets stuck at `generating`. Per-task time limits are overridden (`soft_time_limit=2700, time_limit=3000`) since a first-run voice-model download, CPU TTS synthesis for a full 15-minute episode, and (on the Ollama path) a script-generation request that can itself legitimately run up to ~27 minutes worst-case at max episode length can together exceed the global 900s default. The per-turn synthesis loop collects `(turn, host, duration)` triples and hands them to `podcast_script.py::build_episode_records()` — a pure function, deliberately pulled out of the Celery task body so it's unit-testable without a live task run (the task uses its own `SessionLocal()`, invisible to the test suite's SAVEPOINT-scoped `db_session` fixture) — which resolves each turn's `host_id` to a `host_name` for the persisted transcript (older episodes predating this only have `host_id`; the frontend falls back to showing that) and builds `episode.shownotes` (one bookmark per story at its first-mentioned turn: title, source name, source URL, `start_seconds`).
- **Serving**: `services/range_streaming.py::range_response()` implements HTTP Range (206 Partial Content) so the frontend `<audio>` element's native seek/scrub works against `GET /api/podcasts/episodes/{id}/audio`. Shownote bookmarks in the UI seek this same `<audio>` element via a ref rather than reloading it.
- **Cover image** (`api/podcasts.py`'s `/shows/{id}/cover` routes): optional per-show image, stored on disk under `settings.podcast_audio_dir/covers/<show_id>.<ext>` — reuses the existing `podcast-audio` volume rather than provisioning a second one just for cover art. Content-type is restricted to PNG/JPEG/WebP and capped at 5MB; bytes are stored and served back as-is, no re-encoding. Served two ways: `GET /shows/{id}/cover` (authenticated, cookie-based — used directly as an `<img src>` in the settings UI since the session cookie covers it automatically) and `GET /public/{feed_token}/cover` (unauthenticated, for the RSS `<itunes:image>`). Falls back to the app's own PWA icon (`icon-512.png`, already publicly served) when unset.
- **Public feed link** (`services/podcast_feed.py`, `api/podcasts.py`'s `/public/*` routes): the app's *first* unauthenticated, public-facing endpoints — a podcast app can't do cookie/`Authorization`-header auth, so `GET /public/{feed_token}/feed.xml`, `GET /public/{feed_token}/episodes/{id}/audio`, and `GET /public/{feed_token}/cover` take no `Depends(get_current_user)` at all, scoped only by `PodcastShow.public_feed_token` (a `secrets.token_urlsafe(32)` embedded in the URL path). Unlike `ApiToken`, this token is stored **in plaintext, not hashed** — deliberately: users need to re-view/re-copy the URL repeatedly (a second device, double-checking what they shared) without it breaking like a rotated credential would; "regenerate" is a separate explicit action for when rotation is actually wanted. `public_feed_enabled` is a second, independent column so disabling pauses serving without discarding the token (re-enabling reuses the same URL). The audio route's one critical check: it verifies `episode.show_id == show.id` (the show resolved *from the token*), not just "episode exists and is ready" — otherwise a valid token for show A could pull show B's audio by guessing an episode id. All three routes are rate-limited (`@limiter.limit("60/minute")`, same decorator as `/api/auth/login`) since they're polled by external podcast-app servers, not just this app's own logged-in users. Requires `PUBLIC_BASE_URL` configured (RSS `<enclosure>` needs a fully-qualified URL; deriving it from the incoming request is unreliable behind Traefik/nginx here) — enabling without it set returns a 400 rather than emitting a broken URL. The feed's `<description>` uses the show's `description` field when set (falling back to a generated default), and each `<item>`'s `<description>` lists that episode's shownotes (title, source, link) when available, falling back to the joined transcript text for older episodes without shownotes. XML is hand-built with stdlib `xml.etree.ElementTree` (RSS2 + iTunes namespace is a shallow schema; no `feedgen`/`PyRSS2Gen` dependency needed).

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app; mounts routers under `/api`; slowapi rate-limit middleware on `/api/auth`; creates/repairs the default admin user from `ADMIN_USERNAME`/`ADMIN_PASSWORD` at startup (`_ensure_default_user`)
- **`config.py`** — All settings loaded from `.env` via Pydantic `Settings`, `lru_cache`d
- **`limiter.py`** — slowapi `Limiter` instance (login: 5/minute)
- **`models/`** — SQLAlchemy models: `NewsItem`, `NewsCluster`, `Source`, `Category`, `CategoryWeight`, `KeywordWeight`, `CategoryKeywordWeight`, `KeywordCluster` (+ snapshots), `LLMBatch`, `PushSubscription`, `ApiToken`, `UserSettings`, `UserTab`, `User`, `PodcastShow`, `PodcastEpisode`
- **`schemas/`** — Pydantic request/response DTOs
- **`api/`** — Route handlers: `news`, `sources`, `categories`, `settings`, `auth`, `clusters`, `stats`, `tabs`, `push`, `learning`, `tokens`, `podcasts`
- **`services/`**:
  - `llm/` — Pluggable provider factory + fallback wrapper (see above); `batch_service.py` handles Anthropic Batch API submission/result-application/cross-user propagation; `generate_podcast_script` (concrete on `LLMProvider`) for podcast scripts
  - `fetchers/` — Registry/factory pattern (`register_fetcher("<type>")` decorator + `get_fetcher`): `RSSFetcher`, `RedditFetcher`, `IMAPFetcher` (newsletters), `MastodonFetcher`, `ScholarFetcher` (registered as `arxiv` — queries arXiv's API directly, not Google Scholar despite the class name), `AtomFetcher`, `LemmyFetcher`, `GitHubFetcher`, `BlueskyFetcher`, `TelegramFetcher`, `ScraperFetcher`. New fetchers register themselves on import — `fetch_tasks.py` imports every fetcher module for its side effect. YouTube and the `scholar` type-name alias were removed (migration `0050_remove_youtube_scholar_types`)
  - `clustering.py` — two-pass clustering, see above
  - `embedding.py` — Ollama embedding generation for semantic clustering
  - `scoring.py` — dynamic category/keyword weight computation; `decay_learned_weights` uses bulk SQL (`UPDATE`/`DELETE`, not ORM loops) to avoid `StaleDataError` under concurrent writes
  - `keyword_clustering.py` — groups related learned keywords into `KeywordCluster`s
  - `feed_ranking.py` — `build_feed()`, the Relevant/Impact/Newest ranking; shared by the feed API and podcast item selection
  - `deduplication.py` — SHA256 of canonicalized URL (tracking/session/cache-busting params stripped, sorted, fragment dropped) for `url_hash`; separate `content_hash` (first 2000 chars) catches same content re-published under a different URL
  - `push_service.py` — Web Push (VAPID) notifications for high-relevance items/clusters
  - `scraper_assist.py` — helper for the generic `ScraperFetcher`
  - `normalization.py` — keyword normalization shared by clustering/scoring
  - `podcast_script.py`, `podcast_scheduling.py`, `range_streaming.py`, `tts/` — see "Podcast pipeline" above
- **`tasks/`** — `celery_app.py` defines the Celery app + full beat schedule; `fetch_tasks.py`, `process_tasks.py`, `podcast_tasks.py` hold the task implementations described above; four queues: `fetch`, `process`, `podcast`, `default`

### Frontend (`frontend/src/`)

- **`App.tsx`** — React Router: `/login` → `LoginPage`, `/` → `FeedPage`, `/podcasts` → `PodcastsPage`, `/settings` → `SettingsPage`, wrapped in `RequireAuth` (redirects to `/login` only on a real 401 — network/5xx errors show a retry screen instead) and a PWA update banner (`registerType: "prompt"`)
- **`api/`** — Axios HTTP client and typed endpoint wrappers, one file per resource
- **`stores/`** — Zustand: `filterStore` (active tab, category/source filters), `preferencesStore` (theme, etc.)
- **`hooks/`** — TanStack Query hooks for server state; `useInfiniteNews` has `staleTime: 60_000`
- **`components/`** — `layout/`, `feed/`, `settings/`, `icons/`, `ui/`
- **`i18n/`** — `react-i18next` with per-language files (20+ languages: `en`, `de`, `fr`, `es`, `it`, `pt`, `nl`, `pl`, `ru`, `uk`, `zh`, `ja`, `ko`, `tr`, `cs`, `da`, `fi`, `hu`, `nb`, `ro`, `sv`)

### Other components

- **`mcp_server/`** — standalone MCP server (`server.py`) exposing a running Shoebill instance to Claude/MCP clients via its REST API, authenticated with a per-user API token (Settings → Preferences → API Tokens → `ApiToken` model / `api/tokens.py`). Run with `uv run --with mcp --with httpx server.py`; configured via `SHOEBILL_API_URL` / `SHOEBILL_API_TOKEN` env vars. Independent of the Docker Compose stack.
- **`tts_service/`** — standalone, independently-deployable TTS container (FastAPI, with a pluggable `TTS_ENGINE` — `piper` or `kokoro`), so podcast synthesis can run on separate hardware from the main stack. See "TTS" under Podcast pipeline above for the full breakdown; deployed via `docker-compose.tts.yml`, consumed by the backend via `TTS_PROVIDER=network`.

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
- **Pluggable TTS**: mirrors the pluggable-LLM pattern (`services/tts/`, `TTS_PROVIDER` env var). `piper` (in-process) and `network` (talks to the standalone `tts_service/` container, see above) exist today; the interface (`list_voices`/`synthesize`) is deliberately minimal so a cloud provider (OpenAI TTS/ElevenLabs) could be added later without redesign.
- **Per-user timezone scheduling**: podcast dispatch is the only feature where Beat's fixed global UTC crontabs aren't enough — see "Podcast pipeline" above for how the per-show variability is pushed into `due_shows()` instead of Beat config.

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
TTS_PROVIDER                 # default: piper (in-process) | network (talks to tts_service/, see below)
TTS_SERVICE_URL                # required when TTS_PROVIDER=network, e.g. http://tts-host:8100
TTS_SERVICE_TIMEOUT            # default: 120s; per-request timeout for TTS_PROVIDER=network
PUBLIC_BASE_URL                # required to enable a podcast show's public feed link; no trailing slash
VITE_ALLOWED_HOSTS            # dev stack only; comma-separated Host headers Vite's dev server will accept
```
