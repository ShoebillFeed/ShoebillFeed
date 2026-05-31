import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.models import NewsCluster, NewsItem
from app.models.user import User
from app.schemas.news_item import NewsClusterOut
from app.services.scoring import update_category_weight, update_keyword_weights

router = APIRouter()


def _load(cluster_id: uuid.UUID, db: Session, user_id: uuid.UUID | None = None) -> NewsCluster:
    q = select(NewsCluster).options(
        joinedload(NewsCluster.items).joinedload(NewsItem.source),
    ).where(NewsCluster.id == cluster_id)
    if user_id:
        q = q.where(NewsCluster.user_id == user_id)
    cluster = db.scalar(q)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


def _get_cluster(cluster_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> NewsCluster:
    cluster = db.scalar(select(NewsCluster).where(NewsCluster.id == cluster_id, NewsCluster.user_id == user_id))
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.patch("/{cluster_id}/read", response_model=NewsClusterOut)
def toggle_read(cluster_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cluster = _get_cluster(cluster_id, db, current_user.id)
    cluster.is_read = not cluster.is_read
    if cluster.is_read:
        cluster.last_read_at = datetime.now(timezone.utc)
    db.commit()
    return _load(cluster_id, db, current_user.id)


@router.patch("/{cluster_id}/relevant", response_model=NewsClusterOut)
def toggle_relevant(cluster_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cluster = _get_cluster(cluster_id, db, current_user.id)
    cluster.is_relevant = not cluster.is_relevant
    db.commit()
    if cluster.is_relevant:
        for cat in cluster.categories:
            update_category_weight(db, cat.id)
        if cluster.extracted_keywords:
            update_keyword_weights(db, cluster.extracted_keywords, current_user.id)
    return _load(cluster_id, db, current_user.id)


@router.patch("/{cluster_id}/read-later", response_model=NewsClusterOut)
def toggle_read_later(cluster_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cluster = _get_cluster(cluster_id, db, current_user.id)
    cluster.read_later = not cluster.read_later
    db.commit()
    return _load(cluster_id, db, current_user.id)


@router.delete("/{cluster_id}", status_code=204)
def delete_cluster(cluster_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cluster = _get_cluster(cluster_id, db, current_user.id)
    db.delete(cluster)
    db.commit()
