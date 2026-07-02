import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import news, sources, categories, settings as settings_router, clusters, stats as stats_router, tabs as tabs_router
from app.api import auth as auth_router
from app.api import push as push_router
from app.api import learning as learning_router
from app.api import tokens as tokens_router

logger = logging.getLogger(__name__)


def _ensure_default_user() -> None:
    from app.config import get_settings
    settings = get_settings()
    if not settings.admin_username or not settings.admin_password:
        return
    from app.database import SessionLocal
    from app.models.user import User
    from app.services.auth import hash_password, verify_password
    from sqlalchemy import select
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == settings.admin_username))
        if not existing:
            db.add(User(
                username=settings.admin_username,
                hashed_password=hash_password(settings.admin_password),
                is_admin=True,
            ))
            db.commit()
            logger.info("Created default admin user '%s'", settings.admin_username)
        else:
            changed = False
            if not existing.is_admin:
                existing.is_admin = True
                changed = True
                logger.info("Promoted '%s' to admin", settings.admin_username)
            try:
                password_matches = verify_password(settings.admin_password, existing.hashed_password)
            except ValueError:
                password_matches = False
            if not password_matches:
                existing.hashed_password = hash_password(settings.admin_password)
                changed = True
                logger.info("Reset password for admin user '%s'", settings.admin_username)
            if changed:
                db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_default_user()
    yield


app = FastAPI(title="Shoebill Feed", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(clusters.router, prefix="/api/clusters", tags=["clusters"])
app.include_router(stats_router.router, prefix="/api/stats", tags=["stats"])
app.include_router(tabs_router.router, prefix="/api/tabs", tags=["tabs"])
app.include_router(push_router.router, prefix="/api/push", tags=["push"])
app.include_router(learning_router.router, prefix="/api/learning", tags=["learning"])
app.include_router(tokens_router.router, prefix="/api/tokens", tags=["tokens"])
