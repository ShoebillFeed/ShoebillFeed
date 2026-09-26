# Shoebill Feed

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Backend tests](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/backend-tests.yml)
[![Frontend tests](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/frontend-tests.yml)
[![MCP server tests](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/mcp-tests.yml/badge.svg)](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/mcp-tests.yml)
[![TTS service tests](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/tts-tests.yml/badge.svg)](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/tts-tests.yml)
[![Docs](https://github.com/ShoebillFeed/ShoebillFeed/actions/workflows/docs.yml/badge.svg)](https://shoebillfeed.github.io/ShoebillFeed/)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-sebhoos-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/u/sebhoos)

A self-hosted, open-source news aggregator with LLM-powered summarisation, clustering, and relevance scoring. Shoebill pulls articles from RSS/Atom feeds, Reddit, Mastodon, Lemmy, Bluesky, Telegram, GitHub releases, arXiv, email newsletters, and a generic scraper for sites without a feed — then uses a local (Ollama) or cloud (Anthropic) LLM to summarise, categorise, and cluster them, and learns which topics matter to you over time from nothing but your own 👍/👎 feedback.

Full documentation: **https://shoebillfeed.github.io/ShoebillFeed/**

## Features

- **Multiple source types** — RSS/Atom, Reddit, Mastodon, Lemmy, Bluesky, Telegram, GitHub releases, arXiv, IMAP email newsletters, or a generic scraper for anything else
- **LLM processing** — automatic summaries, keyword extraction, category assignment, relevance/impact scoring, via a local model (Ollama) or a cloud provider (Anthropic), your choice
- **Relevance learning** — the more you like/dislike articles, the better the feed gets ranked; every learned weight is visible and adjustable in Settings, never a black box
- **Clustering** — related articles from different sources are grouped into one card with a synthesized summary of the common ground
- **AI podcast** — configure up to three AI hosts, each with a text-promptable character, to discuss your top stories on a daily schedule; voices are generated locally, no cloud TTS service required. Three engines to choose from (Piper, Kokoro, or Chatterbox's voice cloning), and synthesis can run in-process or be offloaded to a separate machine with a GPU. Episodes are playable in the app or subscribable in any podcast app via a private RSS link
- **Claude / MCP integration** — a bundled [Model Context Protocol](https://modelcontextprotocol.io/) server exposes your feed to Claude or any MCP client through 33 tools: read and search it, mark and like articles, add sources and categories, ask why something ranks highly and correct it, generate a podcast episode, or find out which topics are gaining ground
- **Scoped API tokens** — each token can be limited to a subset of capabilities (read, act, curate, learning, podcasts, stats), so a read-only client and a fully-privileged one hold different credentials and revoking either is just deleting that token
- **Push notifications** — browser push for high-relevance articles
- **Installable PWA** — add it to your home screen or desktop, works offline with your last-synced feed, and prompts you when an update is available
- **Dark mode** — full light/dark theme support
- **Multi-user** — separate accounts, feeds, and learned preferences on one instance
- **Custom feed tabs** — save a named view filtered by category, source, sort order, and/or unread-only, each with its own icon
- **Article translation** — set a per-user output language in Settings and article titles/summaries are translated automatically as the LLM processes them
- **21 languages** — full UI translation: English, German, French, Spanish, Italian, Portuguese, Dutch, Polish, Russian, Ukrainian, Chinese, Japanese, Korean, Turkish, Czech, Danish, Finnish, Hungarian, Norwegian Bokmål, Romanian, Swedish
- **No ads, no tracking** — nobody but you ever runs your instance

When adding a source (especially the generic scraper), make sure you're configuring it in line with that source's own terms of service — that's on whoever adds the source, not the software.

---

## Quick Start (Docker)

### 1. Clone and configure

```bash
git clone https://github.com/ShoebillFeed/ShoebillFeed.git shoebill_feed
cd shoebill_feed
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Database password |
| `JWT_SECRET` | Random secret — run `openssl rand -hex 32` |
| `ADMIN_PASSWORD` | Initial admin password |
| `LLM_PROVIDERS` | `ollama` or `anthropic` (see [LLM Setup](#llm-setup)) |

### 2. Start

```bash
docker compose up -d
```

The app is served by the `frontend` container. Wire it up via a reverse proxy (e.g. Traefik or Nginx) on port 80. The backend API runs internally on port 8000 and is proxied under `/api`.

For local testing without a reverse proxy, add a port mapping to the `frontend` service in `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "8080:80"
```

Then open `http://localhost:8080`.

### 3. Log in

Use the credentials from `ADMIN_USERNAME` / `ADMIN_PASSWORD` in your `.env`. To reset the admin password, update `ADMIN_PASSWORD` in `.env` and restart — the new password is applied automatically on startup.

---

## Development

### Frontend (hot reload)

```bash
cd frontend
npm install
npm run dev        # Vite dev server on http://localhost:5173
```

### Full stack with hot reload

```bash
docker compose up
```

`docker-compose.override.yml` mounts source directories and enables hot reload for both the frontend (Vite) and backend (uvicorn `--reload`).

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`

### Database migrations

```bash
cd backend
alembic upgrade head

# After changing models:
alembic revision --autogenerate -m "description"
```

### Tests

Four suites, each run by its own CI workflow on changes to its directory.

```bash
# Backend — runs against a real Postgres+pgvector instance:
docker run -d --rm -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=shoebill_test pgvector/pgvector:pg17
cd backend
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/shoebill_test pytest

cd ../frontend
npm test     # Vitest

# MCP server — no services needed, every test stubs the HTTP layer:
cd ../mcp_server
pip install -r requirements-dev.txt && pytest

# TTS service — install torch from the CPU-only index unless you want the
# multi-gigabyte CUDA wheels:
cd ../tts_service
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-dev.txt && pytest
```

---

## LLM Setup

### Ollama (local, recommended for self-hosting)

1. Install [Ollama](https://ollama.com) and pull a model:
   ```bash
   ollama pull gemma3:12b   # or qwen2.5:14b, llama3.1:8b, etc.
   ollama pull nomic-embed-text
   ```
2. Set in `.env`:
   ```
   LLM_PROVIDERS=ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   OLLAMA_MODEL=gemma3:12b
   ```

Alternatively, run Ollama itself in Docker using the provided compose file:
```bash
docker compose -f docker-compose.ollama.yml up -d
```
Then set `OLLAMA_BASE_URL=http://ollama:11434` and connect both stacks to the same Docker network.

### Anthropic (cloud)

```
LLM_PROVIDERS=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5
```

### Fallback chain

Comma-separate providers for ordered fallback:
```
LLM_PROVIDERS=ollama,anthropic   # try Ollama first, fall back to Anthropic
```

---

## Architecture

| Service | Role |
|---|---|
| `postgres` | Primary data store (PostgreSQL 17 + pgvector) |
| `redis` | Celery broker and result backend |
| `backend` | FastAPI REST API |
| `celery-worker` | Fetch queue (all source types) |
| `celery-worker-process` | LLM processing queue (single-concurrency for GPU) |
| `celery-worker-podcast` | Podcast episode generation queue (script + TTS + audio encoding) |
| `celery-beat` | Cron scheduler — fetch every 5 min, process every 15 min |
| `frontend` | React app served by Nginx, proxies `/api` to backend |

Two further components ship in this repo but deliberately run outside that
stack, each deployed on its own:

| Component | Role |
|---|---|
| `mcp_server/` | MCP server exposing your instance to Claude and other MCP clients over its REST API. Needs no database access — it authenticates with an API token like any other client. See [the MCP docs](https://shoebillfeed.github.io/ShoebillFeed/mcp-server.html) |
| `tts_service/` | Optional standalone TTS container (Piper, Kokoro or Chatterbox) so podcast synthesis can run on different hardware than the Celery workers — the same idea as pointing `OLLAMA_BASE_URL` at a GPU box. Deployed via `docker-compose.tts.yml` |

---

## Environment Variables

See `.env.example` for the full list with descriptions.

---

## License

[AGPLv3](LICENSE) — the same license Nextcloud uses, chosen specifically so that anyone hosting a modified version keeps their changes open too.
