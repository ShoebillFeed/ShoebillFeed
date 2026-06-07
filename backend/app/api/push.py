from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.config import get_settings
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.schemas.push import PushSubscriptionCreate, VapidPublicKeyOut

router = APIRouter()


@router.get("/vapid-public-key", response_model=VapidPublicKeyOut)
def get_vapid_public_key():
    settings = get_settings()
    return VapidPublicKeyOut(
        public_key=settings.vapid_public_key,
        configured=bool(settings.vapid_public_key and settings.vapid_private_key),
    )


@router.post("/subscription", status_code=201)
def save_subscription(
    sub: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = db.scalar(
        select(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == sub.endpoint,
        )
    )
    if existing:
        existing.p256dh = sub.p256dh
        existing.auth = sub.auth
    else:
        db.add(PushSubscription(
            user_id=user.id,
            endpoint=sub.endpoint,
            p256dh=sub.p256dh,
            auth=sub.auth,
        ))
    db.commit()
    return {"status": "ok"}


@router.delete("/subscription")
def delete_subscription(
    endpoint: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.execute(
        PushSubscription.__table__.delete().where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == endpoint,
        )
    )
    db.commit()
    return {"status": "ok"}
