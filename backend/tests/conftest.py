import os

# Must be set before any `app.*` module is imported, since app.database binds
# a module-level engine to settings.database_url at import time.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/shoebill_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
# Deliberately unset: leaving ADMIN_USERNAME/ADMIN_PASSWORD unset keeps
# main.py's startup _ensure_default_user() a no-op, so app startup doesn't
# write to the real (non-transactional) database connection during tests.

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.database import engine
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _migrated_db():
    """Run the real Alembic migration chain once against the test database.

    Shells out to the `alembic` CLI rather than importing alembic.command:
    pytest puts BACKEND_DIR on sys.path (tests/ is a package), and this
    project's own migrations directory is also named `alembic`, so an
    in-process `from alembic import command` resolves to backend/alembic/
    instead of the real pip package. Running the actual CLI entry point
    sidesteps that shadowing entirely.
    """
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": os.environ["DATABASE_URL"]},
        check=True,
    )
    yield


@pytest.fixture()
def db_session(_migrated_db):
    """A session bound to a SAVEPOINT that's rolled back after each test.

    Route handlers and service functions call db.commit() internally; a plain
    outer transaction would be prematurely closed by that. Restarting a nested
    SAVEPOINT after each such commit (the standard SQLAlchemy test recipe)
    keeps every test isolated regardless of how many times application code
    commits.
    """
    connection = engine.connect()
    outer_trans = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_trans.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with get_db overridden to the isolated test session.

    Uses an https:// base_url so the app's Secure-flagged auth cookie
    (see api/auth.py's set_cookie(..., secure=True)) is actually retained
    and replayed by httpx's cookie jar across requests within a test.
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, base_url="https://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: create a persisted User row."""
    from app.models.user import User
    from app.services.auth import hash_password

    def _make(username: str = "alice", password: str = "correct horse battery staple", is_admin: bool = False):
        user = User(username=username, hashed_password=hash_password(password), is_admin=is_admin)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_client(client, make_user, db_session):
    """A TestClient already carrying a valid session cookie for a fresh user.

    Builds the JWT directly via create_token() rather than hitting
    /api/auth/login, so tests that just need "some logged-in user" don't
    chip away at that endpoint's 5/minute rate limit (see test_auth_api.py
    for tests that exercise /login itself).
    """
    from app.services.auth import create_token

    user = make_user()
    token = create_token(user.id, user.username)
    client.cookies.set("access_token", token)
    client.current_user = user  # convenience for assertions
    return client
