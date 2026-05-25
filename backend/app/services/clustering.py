import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem

STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "has", "have",
    "had", "will", "would", "could", "should", "may", "might", "its", "this",
    "that", "as", "by", "from", "it", "not", "no", "so", "if", "their",
    "after", "over", "new", "says", "say", "said", "report", "us",
})
SIMILARITY_THRESHOLD = 0.3


def _title_words(title: str) -> frozenset[str]:
    return frozenset(
        w for w in re.sub(r"[^\w\s]", "", title.lower()).split()
        if w not in STOP_WORDS and len(w) > 2
    )


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster_new_items(db: Session, new_item_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID | None]:
    """
    Groups newly-fetched items by title similarity (Jaccard on title words).
    Creates NewsCluster rows and assigns cluster_id on NewsItem objects.
    Does NOT commit — caller must commit.
    Returns {item_id: cluster_id | None}.
    """
    if not new_item_ids:
        return {}

    items = db.scalars(select(NewsItem).where(NewsItem.id.in_(new_item_ids))).all()
    if len(items) < 2:
        return {items[0].id: None} if items else {}

    words = {item.id: _title_words(item.title) for item in items}

    # Union-find
    parent: dict[uuid.UUID, uuid.UUID] = {item.id: item.id for item in items}

    def find(x: uuid.UUID) -> uuid.UUID:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if _jaccard(words[a.id], words[b.id]) >= SIMILARITY_THRESHOLD:
                parent[find(a.id)] = find(b.id)

    # Build root → group mapping
    groups: dict[uuid.UUID, list[NewsItem]] = {}
    for item in items:
        groups.setdefault(find(item.id), []).append(item)

    result: dict[uuid.UUID, uuid.UUID | None] = {}
    for group_items in groups.values():
        if len(group_items) >= 2:
            earliest = min(
                (i.published_at for i in group_items if i.published_at),
                default=None,
            )
            user_id = group_items[0].user_id
            cluster = NewsCluster(published_at=earliest, user_id=user_id)
            db.add(cluster)
            db.flush()
            for item in group_items:
                item.cluster_id = cluster.id
                result[item.id] = cluster.id
        else:
            result[group_items[0].id] = None

    return result
