import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.api_token import ApiToken
from app.models.user import User
from app.services.auth import get_current_user, generate_api_token
from app.services.token_scopes import ALL_SCOPES, normalize_scopes

router = APIRouter()


class TokenCreate(BaseModel):
    name: str
    # None means unrestricted, matching the column default and every token
    # that predates scopes. An explicit [] is a valid, if useless, choice.
    scopes: Optional[list[str]] = None


class TokenResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    last_used_at: Optional[datetime]
    scopes: Optional[list[str]] = None


class ScopeInfo(BaseModel):
    key: str
    description: str


class TokenCreateResponse(TokenResponse):
    token: str


@router.get("", response_model=list[TokenResponse])
def list_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tokens = db.scalars(
        select(ApiToken)
        .where(ApiToken.user_id == current_user.id)
        .order_by(ApiToken.created_at.desc())
    ).all()
    return [
        TokenResponse(
            id=t.id,
            name=t.name,
            created_at=t.created_at,
            last_used_at=t.last_used_at,
            scopes=t.scopes,
        )
        for t in tokens
    ]


@router.get("/scopes", response_model=list[ScopeInfo])
def list_scopes():
    """The capability scopes a token can be limited to, for the settings UI.

    Declared before /{token_id} would ever be a concern -- it isn't here,
    since that route is DELETE-only -- and deliberately not gated on token
    auth, which cannot reach /api/tokens at all (see token_scopes.py).
    """
    return [ScopeInfo(key=key, description=desc) for key, desc in ALL_SCOPES.items()]


@router.post("", response_model=TokenCreateResponse, status_code=201)
def create_token(
    payload: TokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Token name is required")

    plaintext, token_hash = generate_api_token()
    token = ApiToken(
        user_id=current_user.id,
        name=name,
        # Unknown scope names are dropped rather than rejected: a client
        # built against a newer scope list shouldn't fail outright, it should
        # get the subset this server actually understands.
        scopes=normalize_scopes(payload.scopes),
        token_hash=token_hash,
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return TokenCreateResponse(
        id=token.id,
        name=token.name,
        created_at=token.created_at,
        last_used_at=token.last_used_at,
        scopes=token.scopes,
        token=plaintext,
    )


@router.delete("/{token_id}", status_code=204)
def delete_token(
    token_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = db.scalar(
        select(ApiToken).where(
            ApiToken.id == token_id,
            ApiToken.user_id == current_user.id,
        )
    )
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(token)
    db.commit()
