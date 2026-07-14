# Configuration

All configuration is via environment variables, read from `.env` (copy
`.env.example` to start). This page documents every variable; defaults
shown are from `backend/app/config.py`.

## Database & cache

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `phoenix` | Database user |
| `POSTGRES_PASSWORD` | — | Database password (**required**) |
| `POSTGRES_DB` | `phoenix` | Database name |
| `DATABASE_URL` | derived from the above | Full SQLAlchemy connection string; set directly to override |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker/result backend |

## LLM providers

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDERS` | `anthropic` | Comma-separated, ordered list — first is primary, rest are fallbacks. Valid values: `anthropic`, `ollama`. Example: `ollama,anthropic`. The legacy singular `LLM_PROVIDER` is also accepted as an alias. |
| `ANTHROPIC_API_KEY` | — | Required if `anthropic` is in the provider list |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Set to a remote host to use Ollama running elsewhere, e.g. `http://192.168.1.10:11434` |
| `OLLAMA_MODEL` | `qwen3:8b` | |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Used for semantic clustering regardless of which provider handles text generation — 768-dim; changing it requires a schema migration (see {doc}`clustering`) |
| `OLLAMA_TIMEOUT` | `300` (seconds) | Increase for remote or slow Ollama hosts |
| `LLM_BATCH_MAX_WAIT_MINUTES` | `10` | How long to wait for an Anthropic Batch API job before cancelling and falling back to synchronous processing |

See {doc}`llm-providers` for how the fallback chain and batch processing work.

## Reddit

| Variable | Default | Description |
|---|---|---|
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | — | From a Reddit ["personal use script" app](https://www.reddit.com/prefs/apps). Can also be set per-source instead (or in addition) — see {doc}`sources`. |
| `REDDIT_USER_AGENT` | `ShoebillFeed/1.0` | |
| `REDDIT_USERNAME` / `REDDIT_PASSWORD` | — | Only needed for the OAuth "password" grant (script-type apps); without them Shoebill falls back to app-only `client_credentials` auth |

## YouTube

| Variable | Default | Description |
|---|---|---|
| `YOUTUBE_API_KEY` | — | A [YouTube Data API v3](https://console.cloud.google.com/) key. Required for any YouTube source — there's no per-source override. |

## Authentication

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET` | `change-me-in-production` | **Change this.** Generate with `openssl rand -hex 32` |
| `JWT_EXPIRE_HOURS` | `24` | Session length |
| `ADMIN_USERNAME` | — | Default admin account, created (or password-reset) on startup |
| `ADMIN_PASSWORD` | — | |

## Push notifications (Web Push / VAPID)

| Variable | Default | Description |
|---|---|---|
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | — | Generate with:<br />`python -c "from pywebpush import Vapid; v=Vapid(); v.generate_keys(); print('VAPID_PRIVATE_KEY='+v.private_key); print('VAPID_PUBLIC_KEY='+v.public_key)"` |
| `VAPID_SUBJECT` | `mailto:admin@localhost` | |

## Notes

- **Restart required for LLM config changes.** `LLM_PROVIDERS` and related
  settings are read once and cached for the process lifetime — the
  settings UI shows the current LLM configuration but changing it always
  requires editing `.env` and restarting, never just an API call.
- **The backend runs from a built Docker image.** `docker compose run --rm
  backend alembic ...` does *not* pick up local file changes — see
  {doc}`development` for the correct migration workflow.
