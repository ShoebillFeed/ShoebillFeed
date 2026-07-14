# Development

## Local setup

```bash
docker compose up
```

`docker-compose.override.yml` is auto-loaded and mounts source directories
with hot reload — Vite for the frontend, uvicorn `--reload` for the
backend. Frontend: `http://localhost:5173`. Backend API:
`http://localhost:8000`.

For frontend-only work without the rest of the stack:

```bash
cd frontend
npm install
npm run dev
```

## Running the tests

### Backend (pytest)

```bash
cd backend
pip install -r requirements-dev.txt
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/shoebill_test pytest
```

Tests run against a **real** Postgres with the pgvector extension (not
SQLite, not mocks) — several real bugs this project has hit
(`StaleDataError`, cartesian-product query bugs) were specifically about
Postgres/ORM behavior that a fake database wouldn't have caught. The
easiest way to get one locally:

```bash
docker run -d --name shoebill-test-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=shoebill_test \
  -p 5432:5432 pgvector/pgvector:pg17
```

`tests/conftest.py` runs the real Alembic migration chain once per test
session, then gives each test an isolated, rolled-back-after transaction —
so tests can freely call the same code paths the app does (including code
that calls `db.commit()` internally) without leaking state between tests.

```{note}
`conftest.py` shells out to the `alembic` CLI rather than importing
`alembic.command` directly. Pytest puts `backend/` on `sys.path` (since
`tests/` is a package), and this project's own migrations directory is
also named `alembic` — an in-process import resolves to
`backend/alembic/` instead of the real pip package. Running the actual
CLI entry point sidesteps the collision.
```

### Frontend (Vitest)

```bash
cd frontend
npm test          # single run
npm run test:watch
```

Component tests use React Testing Library via a shared
`src/test/render.tsx` helper that wraps `QueryClientProvider` and
`MemoryRouter`.

### CI

Both suites run automatically in GitHub Actions
(`.github/workflows/backend-tests.yml`,
`.github/workflows/frontend-tests.yml`), each scoped to only trigger on
changes to its own half of the repo. The backend workflow spins up a real
`pgvector/pgvector:pg17` service container, same as local development.

## Database migrations

```{important}
The backend runs from a **built Docker image**. `docker compose run --rm
backend alembic ...` does *not* pick up local file changes to the app —
migration files must be written manually, then applied by rebuilding.
```

1. Create a new file in `backend/alembic/versions/`, following the
   existing naming convention (`<NNNN>_<slug>.py`).
2. Set `down_revision` to the current head's `revision` string. Check the
   current head with:
   ```bash
   docker compose run --rm backend alembic heads
   ```
3. Rebuild and apply:
   ```bash
   docker compose up --build
   ```

## Contributing

- Match the existing commit message style: short, specific, imperative
  mood (`"Fix X by doing Y"`, not `"Fixes"` or `"Updates stuff"`).
- No linter/formatter is currently enforced — match the surrounding
  code's style.
- Add tests for new business logic, especially anything touching scoring,
  clustering, or deduplication — these are exactly the areas where a
  subtly wrong edge case is easy to ship unnoticed.
- Shoebill Feed is licensed [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html)
  — contributions are accepted under the same license.
