import logging
import re
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.services.normalization import normalize_keyword

logger = logging.getLogger(__name__)

KEYWORD_SIMILARITY_THRESHOLD = 0.25
MIN_SHARED_KEYWORDS = 2
EMBEDDING_DISTANCE_THRESHOLD = 0.18  # cosine distance ≤ 0.18 ≈ cosine similarity ≥ 0.82

STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "has", "have",
    "had", "will", "would", "could", "should", "may", "might", "its", "this",
    "that", "as", "by", "from", "it", "not", "no", "so", "if", "their",
    "after", "over", "new", "says", "say", "said", "report", "us",
    # Generic news boilerplate that recurs across unrelated stories on the
    # same broad topic and adds little distinguishing signal.
    "plan", "plans", "deal", "deals", "talks", "talk", "war", "amid",
    "calls", "call", "called", "announces", "announce", "announced",
    "set", "sets", "more", "most", "than", "what", "when", "where", "who",
    "why", "how", "all", "out", "up", "down", "off", "now", "just", "can",
    "two", "three", "first", "second", "year", "years", "world", "latest",
    "news", "while", "during", "into", "still", "back", "make", "makes",
    "made",
})
SIMILARITY_THRESHOLD = 0.3
MIN_SHARED_WORDS = 2
LOOKBACK_HOURS = 48


def _keyword_set(item: "NewsItem") -> frozenset[str]:
    if not item.extracted_keywords:
        return frozenset()
    return frozenset(normalize_keyword(kw) for kw in item.extracted_keywords if kw.strip())


def _title_words(title: str) -> frozenset[str]:
    return frozenset(
        normalize_keyword(w)
        for w in re.sub(r"[^\w\s]", "", title.lower()).split()
        if w not in STOP_WORDS and len(w) > 2 and not w.isdigit()
    )


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _matches(a: frozenset, b: frozenset, threshold: float, min_shared: int) -> bool:
    """
    Jaccard similarity check with a minimum absolute-overlap requirement.
    Without this, one or two coincidentally-shared generic terms (e.g. a
    recurring entity name, or a leftover year/number) can push the ratio
    over threshold for small word/keyword sets even when the items are
    about unrelated stories.
    """
    if not a or not b:
        return False
    shared = a & b
    if len(shared) < min_shared:
        return False
    return len(shared) / len(a | b) >= threshold


def cluster_new_items(db: Session, new_item_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID | None]:
    """
    Groups newly-fetched items by title similarity (Jaccard on title words),
    also comparing against recently-fetched items from other sources.
    Creates or extends NewsCluster rows and assigns cluster_id on NewsItem objects.
    Does NOT commit — caller must commit.
    Returns {item_id: cluster_id | None} for new items only.

    When new_item_ids spans multiple users (companion-source fan-out), items are
    grouped by user_id first so clustering never crosses user boundaries.
    """
    if not new_item_ids:
        return {}

    new_item_id_set = set(new_item_ids)
    new_items = db.scalars(select(NewsItem).where(NewsItem.id.in_(new_item_ids))).all()

    # Group by user so clustering stays within each user's data
    by_user: dict[uuid.UUID | None, list[NewsItem]] = {}
    for item in new_items:
        by_user.setdefault(item.user_id, []).append(item)

    result: dict[uuid.UUID, uuid.UUID | None] = {}
    for user_id, user_items in by_user.items():
        result.update(_cluster_for_user(db, user_id, user_items, new_item_id_set))
    return result


def _cluster_for_user(
    db: Session,
    user_id: uuid.UUID | None,
    new_items: list["NewsItem"],
    new_item_id_set: set[uuid.UUID],
) -> dict[uuid.UUID, uuid.UUID | None]:
    """Run the title-Jaccard clustering algorithm for a single user's new items."""
    new_ids = [i.id for i in new_items]

    # Load recent items from other sources for THIS user only
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    q = select(NewsItem).where(
        NewsItem.id.notin_(new_ids),
        NewsItem.fetched_at >= cutoff,
    )
    if user_id is not None:
        q = q.where(NewsItem.user_id == user_id)
    recent_items = db.scalars(q).all()

    all_items = new_items + recent_items
    words = {item.id: _title_words(item.title) for item in all_items}

    # Combined title-word vocabulary per existing cluster among recent_items.
    # A new item must fit a cluster's overall vocabulary, not just match one
    # (possibly tangential) member, to avoid transitively "drifting" into a
    # long-running cluster via a single weak link.
    cluster_anchor_words: dict[uuid.UUID, frozenset[str]] = {}
    for item in recent_items:
        if item.cluster_id is not None:
            cluster_anchor_words[item.cluster_id] = (
                cluster_anchor_words.get(item.cluster_id, frozenset()) | words[item.id]
            )

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
            if _matches(words[a.id], words[b.id], SIMILARITY_THRESHOLD, MIN_SHARED_WORDS):
                parent[find(a.id)] = find(b.id)

    # Compare each new item against recent items from other sources
    for new_item in new_items:
        for recent in recent_items:
            if recent.cluster_id is not None:
                anchor = cluster_anchor_words[recent.cluster_id]
                matched = _matches(words[new_item.id], anchor, SIMILARITY_THRESHOLD, MIN_SHARED_WORDS)
            else:
                matched = _matches(words[new_item.id], words[recent.id], SIMILARITY_THRESHOLD, MIN_SHARED_WORDS)
            if matched:
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
            cluster.title = None
            cluster.is_read = False
            for item in new_in_group:
                item.cluster_id = target_id
                result[item.id] = target_id
        else:
            # All standalone — create a new cluster
            all_dates = [i.published_at for i in group_items if i.published_at]
            earliest = min(all_dates) if all_dates else None
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


def recluster_processed_item(db: Session, item: NewsItem) -> uuid.UUID | None:
    """
    Second-pass clustering after individual LLM processing. Called for standalone items
    (cluster_id is None). Tries two strategies in order:

    1. Embedding cosine distance (primary): queries pgvector for the nearest
       already-processed item within EMBEDDING_DISTANCE_THRESHOLD. Fast and semantic.
       Falls back to (2) if embedding is unavailable or no match is found.

    2. Keyword Jaccard (fallback): scans recently-processed items for keyword overlap
       >= KEYWORD_SIMILARITY_THRESHOLD with a drift guard against cluster vocabulary.

    Does NOT commit — caller must commit and dispatch process_cluster.
    Returns the cluster_id assigned, or None.
    """
    if item.cluster_id is not None:
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    used_embedding = False
    best: NewsItem | None = None
    item_kws: frozenset[str] = frozenset()

    # --- Primary: embedding cosine distance ---
    if item.embedding is not None:
        try:
            best = db.scalars(
                select(NewsItem)
                .where(
                    NewsItem.id != item.id,
                    NewsItem.user_id == item.user_id,
                    NewsItem.llm_processed == True,  # noqa: E712
                    NewsItem.fetched_at >= cutoff,
                    NewsItem.embedding.isnot(None),
                    NewsItem.embedding.cosine_distance(item.embedding) < EMBEDDING_DISTANCE_THRESHOLD,
                )
                .order_by(NewsItem.embedding.cosine_distance(item.embedding))
                .limit(1)
            ).first()
            if best is not None:
                used_embedding = True
        except Exception:
            logger.warning("Embedding recluster lookup failed", exc_info=True)

    # --- Fallback: keyword Jaccard ---
    if best is None and item.extracted_keywords:
        item_kws = _keyword_set(item)
        if item_kws:
            candidates = db.scalars(
                select(NewsItem).where(
                    NewsItem.id != item.id,
                    NewsItem.user_id == item.user_id,
                    NewsItem.llm_processed == True,  # noqa: E712
                    NewsItem.fetched_at >= cutoff,
                    NewsItem.extracted_keywords.isnot(None),
                )
            ).all()

            best_score = 0.0
            for candidate in candidates:
                cand_kws = _keyword_set(candidate)
                if not _matches(item_kws, cand_kws, KEYWORD_SIMILARITY_THRESHOLD, MIN_SHARED_KEYWORDS):
                    continue
                score = _jaccard(item_kws, cand_kws)
                if score > best_score:
                    best_score = score
                    best = candidate

    if best is None:
        return None

    # Re-read best match in case a concurrent task just assigned it to a cluster
    db.refresh(best)

    if best.cluster_id is not None:
        cluster = db.get(NewsCluster, best.cluster_id)
        if cluster is None:
            return None

        # Drift guard (keyword path only): item must fit the cluster's overall keyword
        # vocabulary, not just the single matched member. The embedding path skips this
        # because cosine distance already captures holistic content similarity.
        if not used_embedding and item_kws:
            members = db.scalars(select(NewsItem).where(NewsItem.cluster_id == cluster.id)).all()
            anchor = frozenset().union(*(_keyword_set(m) for m in members))
            if not _matches(item_kws, anchor, KEYWORD_SIMILARITY_THRESHOLD, MIN_SHARED_KEYWORDS):
                return None

        cluster.llm_processed = False
        cluster.unified_abstract = None
        cluster.title = None
        cluster.is_read = False
        item.cluster_id = cluster.id
        return cluster.id
    else:
        all_dates = [i.published_at for i in (item, best) if i.published_at]
        cluster = NewsCluster(
            published_at=min(all_dates) if all_dates else None,
            user_id=item.user_id,
        )
        db.add(cluster)
        db.flush()
        item.cluster_id = cluster.id
        best.cluster_id = cluster.id
        return cluster.id
