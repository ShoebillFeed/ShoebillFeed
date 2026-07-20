# Getting Started

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Either [Ollama](https://ollama.com) (for a fully local, free setup) or an
  [Anthropic API key](https://console.anthropic.com/) (for cloud LLM
  processing) — see {doc}`llm-providers` for the tradeoffs

## 1. Clone and configure

```bash
git clone https://github.com/ShoebillFeed/ShoebillFeed.git shoebill_feed
cd shoebill_feed
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Database password |
| `JWT_SECRET` | Random secret — generate with `openssl rand -hex 32` |
| `ADMIN_PASSWORD` | Initial admin account password |
| `LLM_PROVIDERS` | `ollama` or `anthropic` — see {doc}`llm-providers` |

The full variable reference can be found in {doc}`configuration`.

## 2. Start the stack

```bash
docker compose up -d
```

This starts Postgres (with pgvector), Redis, the FastAPI backend, two
Celery workers (fetch and LLM-processing queues), Celery Beat, and the
frontend.

The app is served by the `frontend` container on port 80. Wire it up
behind a reverse proxy (Traefik, Nginx — see {doc}`deployment`), or for
local testing without one, add a port mapping in `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "8080:80"
```

Then open `http://localhost:8080`.

## 3. Log in

Use the credentials from `ADMIN_USERNAME`/`ADMIN_PASSWORD` in your `.env`.
To reset the admin password later, change `ADMIN_PASSWORD` and restart —
the new password is applied automatically on startup.

## 4. Add your first categories

In **Settings → Categories**, define a few topics you care about — each
needs a name, and optionally a color, keywords, and a prompt fragment
giving the LLM extra context on what belongs in it. Don't want to write
them by hand? The "Default Categories" browser lets you pull ready-made
ones from a built-in IPTC-based taxonomy instead. See {doc}`user-guide`
for details.

## 5. Add your first source

In **Settings → Sources**, add an RSS feed, a subreddit, or any other
source type (see {doc}`sources` for the full list and each type's exact
configuration). Sources are fetched on a schedule (every 5 minutes by
default) and new items are processed by the LLM shortly after.
