# Configuration

Configuration is organized by setting environment variables, read from
`.env` (copy `.env.example` to start). This page documents every
variable; defaults shown are from `backend/app/config.py`.

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
| `OLLAMA_TIMEOUT` | `300` (seconds) | Floor, not a fixed value — increase for remote or slow Ollama hosts. Large generations (notably the podcast script) automatically use a longer per-request timeout above this floor, scaled to how much output was requested. |
| `LLM_BATCH_MAX_WAIT_MINUTES` | `10` | How long to wait for an Anthropic Batch API job before cancelling and falling back to synchronous processing |

See {doc}`llm-providers` for how the fallback chain and batch processing work.

## Podcast (text-to-speech)

| Variable | Default | Description |
|---|---|---|
| `TTS_PROVIDER` | `piper` | Text-to-speech backend for generated podcast episodes. `piper` runs self-hosted Piper in-process (CPU-only, no GPU or API key needed; voice models are downloaded automatically on first use into the `piper-voices` Docker volume). `network` instead talks over HTTP to a standalone `tts_service/` container (see {doc}`deployment`) — use this to run synthesis on separate hardware, e.g. a GPU machine. |
| `TTS_SERVICE_URL` | — | Required when `TTS_PROVIDER=network`, e.g. `http://tts-host:8100`. |
| `TTS_SERVICE_TIMEOUT` | `120` (seconds) | Per-request timeout when `TTS_PROVIDER=network`. Increase for a slow/remote/CPU-only TTS host. |
| `PUBLIC_BASE_URL` | — | Required to enable a podcast show's public feed link (subscribing in a real podcast app). Must be the fully-qualified, publicly-reachable URL your instance is served at, no trailing slash, e.g. `https://shoebill.example.com`. Leave unset to keep the feature disabled — the enable button then returns a clear error instead of emitting a broken URL. |

`PIPER_MODEL_DIR` and `PODCAST_AUDIO_DIR` are fixed container paths (not
meant to be overridden) backed by the `piper-voices` and `podcast-audio`
named volumes — see {doc}`deployment`.

### Running TTS synthesis on separate hardware

`docker-compose.tts.yml` runs a standalone TTS container independent of
the main stack — the same pattern as `docker-compose.ollama.yml` for LLM
calls. Point the main stack at it and it takes over podcast synthesis:

```bash
# On the TTS machine (CPU):
docker compose -f docker-compose.tts.yml up -d --build

# On the TTS machine (GPU):
TTS_GPU=true TTS_DEVICE=cuda docker compose -f docker-compose.tts.yml up -d --build
# (also uncomment the NVIDIA deploy block in docker-compose.tts.yml)

# In the main stack's .env:
TTS_PROVIDER=network
TTS_SERVICE_URL=http://<tts-machine-ip>:8100
```

GPU use is opt-in at two independent points, both off by default: the
`TTS_GPU` build arg (whether the image has GPU-capable builds of the ML
backends instead of their CPU-only defaults) and `TTS_DEVICE=cuda` at
runtime (whether the engine is actually told to use it). A CPU-only
deployment needs neither — except practically speaking for `chatterbox`
(below), which is slow enough on CPU (~10x real-time) that GPU is worth
having for it specifically.

**`TTS_ENGINE`** picks which synthesis backend `tts_service/` runs (default
`piper`; `kokoro` and `chatterbox` also available) — all three are always
installed in the image, so this is a plain env var change, no rebuild
needed:

```bash
TTS_ENGINE=kokoro docker compose -f docker-compose.tts.yml up -d --build
```

`piper` (self-hosted, CPU/ONNX, GPL-3.0) is the original engine and covers
the widest fixed-voice language list. `kokoro` ([hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M),
Apache 2.0) offers a smaller set of languages (English, Spanish, French,
Italian, Portuguese) but with distinctly higher-quality, named voices
(`af_heart`, `bm_daniel`, etc.) rather than Piper's numbered speakers —
worth trying if Piper's default English voice quality isn't good enough
for your use case. `chatterbox` ([ResembleAI/chatterbox](https://github.com/resemble-ai/chatterbox),
MIT) works differently from the other two: instead of picking a named
voice, it clones one from a short reference audio clip. It ships one
built-in `default` voice per supported language (English, German, French,
Spanish, Italian, Dutch, Polish, Portuguese, Russian, Chinese, Japanese,
Korean, Turkish, Swedish, Danish, Finnish, Norwegian), and you can add more
by dropping a `.wav` clip into
`{TTS_MODEL_DIR}/chatterbox_voices/{language}/your-voice-name.wav` on the
TTS host — no restart needed, it's rescanned on every request. Meaningfully
slower than the other two engines, so it's the one where the GPU option
actually matters.

## Reddit

| Variable | Default | Description |
|---|---|---|
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | — | From a Reddit ["personal use script" app](https://www.reddit.com/prefs/apps). Can also be set per-source instead (or in addition) — see {doc}`sources`. |
| `REDDIT_USER_AGENT` | `ShoebillFeed/1.0` | |
| `REDDIT_USERNAME` / `REDDIT_PASSWORD` | — | Only needed for the OAuth "password" grant (script-type apps); without them Shoebill falls back to app-only `client_credentials` auth |

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
