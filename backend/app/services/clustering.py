import re
import uuid
from datetime import datetime, timezone, timedelta

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
LOOKBACK_HOURS = 48


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
    Groups newly-fetched items by title similarity (Jaccard on title words),
    also comparing against recently-fetched items from other sources.
    Creates or extends NewsCluster rows and assigns cluster_id on NewsItem objects.
    Does NOT commit — caller must commit.
    Returns {item_id: cluster_id | None} for new items only.
    """
    if not new_item_ids:
        return {}

    new_item_id_set = set(new_item_ids)
    new_items = db.scalars(select(NewsItem).where(NewsItem.id.in_(new_item_ids))).all()

    # Load recent items from other sources to enable cross-source clustering
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    recent_items = db.scalars(
        select(NewsItem).where(
            NewsItem.id.notin_(new_item_ids),
            NewsItem.fetched_at >= cutoff,
        )
    ).all()

    all_items = new_items + recent_items
    words = {item.id: _title_words(item.title) for item in all_items}

    # Union-find over all items
    parent: dict[uuid.UUID, uuid.UUID] = {item.id: item.id for item in all_items}

    def find(x: uuid.UUID) -> uuid.UUID:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # Compare new items pairwise
    for i, a in enumerate(new_items):
        for b in new_items[i + 1:]:
            if _jaccard(words[a.id], words[b.id]) >= SIMILARITY_THRESHOLD:
                parent[find(a.id)] = find(b.id)

    # Compare each new item against recent items from other sources
    for new_item in new_items:
        for recent in recent_items:
            if _jaccard(words[new_item.id], words[recent.id]) >= SIMILARITY_THRESHOLD:
                parent[find(new_item.id)] = find(recent.id)

    # Build root → group mapping (only groups that contain at least one new item)
    groups: dict[uuid.UUID, list[NewsItem]] = {}
    for item in all_items:
        groups.setdefault(find(item.id), []).append(item)

    result: dict[uuid.UUID, uuid.UUID | None] = {}

    for group_items in groups.values():
        new_in_group = [i for i in group_items if i.id in new_item_id_set]
        if not new_in_group:
            continue  # all-old group, nothing to do

        if len(group_items) < 2:
            result[new_in_group[0].id] = None
            continue

        # Find existing clusters among the group
        existing_cluster_ids = [i.cluster_id for i in group_items if i.cluster_id is not None]

        if existing_cluster_ids:
            # Add new items to the existing cluster (pick the most common one)
            target_id = max(set(existing_cluster_ids), key=existing_cluster_ids.count)
            cluster = db.get(NewsCluster, target_id)
            # Reset so the cluster gets reprocessed with the new member
            cluster.llm_processed = False
            cluster.unified_abstract = None
            for item in new_in_group:
                item.cluster_id = target_id
                result[item.id] = target_id
        else:
            # All standalone — create a new cluster
            all_dates = [i.published_at for i in group_items if i.published_at]
            earliest = min(all_dates) if all_dates else None
            user_id = group_items[0].user_id
            cluster = NewsCluster(published_at=earliest, user_id=user_id)
            db.add(cluster)
            db.flush()
            for item in group_items:
                item.cluster_id = cluster.id
                result[item.id] = cluster.id

    # New items not matched to any group
    for item in new_items:
        if item.id not in result:
            result[item.id] = None

    return result
