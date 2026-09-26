import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: uuid.UUID, username: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def generate_api_token() -> tuple[str, str]:
    """Return (plaintext_token, sha256_hex_hash)."""
    plaintext = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    return plaintext, token_hash


def get_current_user(request: Request, db: Session = Depends(get_db)):
    from app.models.user import User
    from app.models.api_token import ApiToken
    from app.services.token_scopes import ScopeDenied, check_request

    # Bearer token takes priority over cookie
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw = auth_header[7:].strip()
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        api_token = db.scalar(
            select(ApiToken).where(ApiToken.token_hash == token_hash)
        )
        if not api_token:
            raise HTTPException(status_code=401, detail="Invalid API token")
        # Scope check before anything else this token could touch. Done here
        # rather than per-route because this is the only place that knows the
        # request authenticated with a token rather than a browser session --
        # and because the MCP server is a client holding one of these, so
        # filtering tools there would be cosmetic. See token_scopes.py.
        route = request.scope.get("route")
        route_path = getattr(route, "path", None) or request.url.path
        try:
            check_request(api_token.scopes, request.method, route_path)
        except ScopeDenied as denied:
            if denied.scope is None:
                raise HTTPException(
                    status_code=403,
                    detail="API tokens cannot access this endpoint",
                )
            raise HTTPException(
                status_code=403,
                detail=f"This API token lacks the '{denied.scope}' scope",
            )

        # Exposed for /api/settings/token-scopes, which reports a token its
        # own capabilities; nothing else should reach for this.
        request.state.api_token = api_token

        api_token.last_used_at = datetime.now(timezone.utc)
        db.commit()
        user = db.scalar(
            select(User).where(User.id == api_token.user_id, User.is_active == True)  # noqa: E712
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.scalar(
        select(User).where(User.id == uuid.UUID(user_id_str), User.is_active == True)  # noqa: E712
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
