# Shoebill Feed

A self-hosted news aggregator with LLM-powered categorisation and relevance scoring. Shoebill fetches articles from RSS feeds, Reddit, YouTube and email newsletters, uses a local or cloud LLM to summarise and categorise them, and learns which topics matter to you over time based on your feedback.

## Features

- **Multiple source types** — RSS/Atom, Reddit, YouTube, IMAP email
- **LLM processing** — automatic summaries, keyword extraction, category assignment, impact scoring
- **Relevance learning** — the more you like/dislike articles, the better the feed gets ranked
- **Clustering** — related articles from different sources are grouped together
- **Push notifications** — browser push for high-relevance articles
- **Dark mode** — full light/dark theme support
- **Multi-user** — separate feeds and preferences per account

---

## Quick Start (Docker)

### 1. Clone and configure

```bash
git clone <repo-url>
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
| `celery-worker` | Fetch queue (RSS, Reddit, YouTube, email) |
| `celery-worker-process` | LLM processing queue (single-concurrency for GPU) |
| `celery-beat` | Cron scheduler — fetch every 5 min, process every 15 min |
| `frontend` | React app served by Nginx, proxies `/api` to backend |

---

## Environment Variables

See `.env.example` for the full list with descriptions.
