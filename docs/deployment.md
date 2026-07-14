# Deployment

## Production compose

```bash
docker compose -f docker-compose.yml up -d
```

This is the same file used in {doc}`getting-started`, without the
dev-only `docker-compose.override.yml` hot-reload mounts. The `frontend`
container serves the built React app via Nginx and proxies `/api` to the
backend — it publishes no host port by default, since it's meant to sit
behind a reverse proxy.

## Reverse proxy

Point a reverse proxy at the `frontend` container on port 80, terminating
TLS there. With [Traefik](https://traefik.io/traefik/), for example, add
labels to the `frontend` service:

```yaml
frontend:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.shoebill.rule=Host(`your-domain.example`)"
    - "traefik.http.routers.shoebill.entrypoints=web"
    - "traefik.http.routers.shoebill-secure.rule=Host(`your-domain.example`)"
    - "traefik.http.routers.shoebill-secure.entrypoints=web-secure"
    - "traefik.http.routers.shoebill-secure.tls=true"
    - "traefik.http.routers.shoebill-secure.tls.certresolver=letsencrypt"
  networks: [shoebill_internal, shoebill]  # shoebill = external network shared with Traefik
```

For local testing without any reverse proxy, add a direct port mapping
instead:

```yaml
frontend:
  ports:
    - "8080:80"
```

### Why the auth cookie needs real TLS

The session cookie is set with `secure=True`, `httponly=True`,
`samesite="strict"`. `secure=True` is safe specifically *because* a
TLS-terminating proxy sits in front — the proxy talks to the browser over
HTTPS and forwards to `frontend`/`backend` over plain HTTP internally, so
the browser still only ever sees the cookie over an encrypted connection.
Running the production compose file directly on plain HTTP (no reverse
proxy, no TLS) means the browser will silently refuse to send the cookie
back, and login will appear to succeed but every subsequent request will
be unauthenticated.

## Volumes and persistence

| Volume | Contents |
|---|---|
| `postgres` data volume | All application data |
| `celerybeat-data` | The Beat scheduler's persisted schedule, so scheduled tasks don't reset on restart |

Back up the Postgres volume; everything else is reproducible from
config + migrations.

```{note}
Backend/Celery containers run as UID 1000, not root. If `celerybeat-data`
already exists owned by root (e.g. from an older setup, or a manual
`docker volume create`), the container will fail to write to it on
startup — remove it and let Docker recreate it with the correct ownership:
`docker volume rm shoebill_feed_celerybeat-data`.
```

## Scaling notes

- `celery-worker` (fetch + default queues) can run with higher
  concurrency safely — fetching is I/O-bound.
- `celery-worker-process` (LLM processing) is deliberately concurrency 1
  when backed by a single local Ollama instance/GPU — see
  {doc}`architecture` for why. If you're running Anthropic (or multiple
  Ollama instances behind a load balancer), raising this concurrency is
  reasonable.
- Fetches for identical sources shared across users are automatically
  deduplicated (see {doc}`architecture`), so adding more users doesn't
  multiply outbound HTTP requests to the same feeds.

## Upgrading

Migrations run automatically as part of the backend image's startup.
Pull the new images (or rebuild), then:

```bash
docker compose pull   # or: docker compose build
docker compose up -d
```

See {doc}`development` for how migrations are written, if you're running
a fork with local schema changes.
