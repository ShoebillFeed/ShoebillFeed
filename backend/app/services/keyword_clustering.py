"""
Embedding-based keyword cluster discovery.

For each active category per user with enough starred articles, we:
1. Fetch starred article embeddings + keywords
2. Greedy union-find clustering via pure-Python cosine distance (no sklearn needed)
3. Compute TF-IDF per cluster to find representative keywords
4. Ask the LLM to give each cluster a short human-readable label
5. Write to keyword_clusters table — used at feed ranking time for synonym expansion

The cluster weight for an unknown keyword is the max CategoryKeywordWeight of any
keyword in the same cluster, so synonyms the user never explicitly starred still
benefit from related articles they did star.
"""
import json
import logging
import math
import uuid
from collections import defaultdict

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models import Category, NewsItem
from app.models.category_keyword_weight import CategoryKeywordWeight
from app.models.keyword_cluster import KeywordCluster
from app.models.news_item import news_item_categories
from app.services.normalization import normalize_keyword

logger = logging.getLogger(__name__)

MIN_STARRED = 5        # minimum starred articles needed to attempt clustering
CLUSTER_DISTANCE = 0.3  # cosine distance threshold for two articles to be in the same cluster
TOP_KEYWORDS_PER_CLUSTER = 20

CLUSTER_NAMING_PROMPT = """Name the keyword clusters below. Each cluster was discovered from a user's liked news articles in the "{category}" category.

For each cluster, return a short (2-5 word) human-readable English label that captures its specific topic. Be concrete and specific — prefer "EU AI Act compliance" over "AI regulation".

Clusters (index → top keywords):
{clusters_json}

Return ONLY a JSON object mapping cluster index (as a string) to its label.
Example: {{"0": "EU AI Act compliance", "1": "battery supply chain"}}"""


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - dot / (norm_a * norm_b)


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        px, py = self.find(x), self.find(y)
        if px != py:
            self.parent[px] = py


def _cluster_articles(embeddings: list[list[float]]) -> list[int]:
    """Return cluster label per article using greedy union-find."""
    n = len(embeddings)
    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if _cosine_distance(embeddings[i], embeddings[j]) < CLUSTER_DISTANCE:
                uf.union(i, j)
    # Normalise: map root ids to sequential 0..K-1 indices
    root_to_idx: dict[int, int] = {}
    labels = []
    for i in range(n):
        root = uf.find(i)
        if root not in root_to_idx:
            root_to_idx[root] = len(root_to_idx)
        labels.append(root_to_idx[root])
    return labels


def _tfidf_keywords(
    cluster_labels: list[int],
    all_keywords: list[list[str]],
    n_clusters: int,
) -> dict[int, list[tuple[str, float]]]:
    """Return top keywords per cluster sorted by TF-IDF score descending."""
    n_docs = len(cluster_labels)

    # Document frequency across all articles
    df: dict[str, int] = defaultdict(int)
    for kws in all_keywords:
        for kw in set(kws):
            df[kw] += 1

    # Term frequency within each cluster
    cluster_kw_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    cluster_sizes: dict[int, int] = defaultdict(int)
    for i, label in enumerate(cluster_labels):
        cluster_sizes[label] += 1
        for kw in all_keywords[i]:
            cluster_kw_counts[label][kw] += 1

    result: dict[int, list[tuple[str, float]]] = {}
    for ci in range(n_clusters):
        size = cluster_sizes.get(ci, 0)
        if size == 0:
            result[ci] = []
            continue
        scores: list[tuple[str, float]] = []
        for kw, count in cluster_kw_counts[ci].items():
            tf = count / size
            idf = math.log(n_docs / (df[kw] + 1)) + 1
            scores.append((kw, tf * idf))
        scores.sort(key=lambda x: x[1], reverse=True)
        result[ci] = scores[:TOP_KEYWORDS_PER_CLUSTER]
    return result


def _generate_cluster_labels(
    category_name: str,
    top_kws: dict[int, list[tuple[str, float]]],
    llm_provider,
) -> dict[int, str]:
    """Call the LLM to produce a human-readable label for each cluster. Falls back to top keyword."""
    clusters_json = {
        str(ci): [kw for kw, _ in keywords[:8]]
        for ci, keywords in top_kws.items()
        if keywords
    }
    if not clusters_json:
        return {}

    prompt = CLUSTER_NAMING_PROMPT.format(
        category=category_name,
        clusters_json=json.dumps(clusters_json, ensure_ascii=False),
    )
    try:
        text = llm_provider._complete(
            system="You are a precise text labeller. Respond only with valid JSON.",
            user=prompt,
            max_tokens=512,
        )
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return {int(k): str(v).strip() for k, v in data.items() if str(v).strip()}
    except Exception:
        logger.exception("LLM cluster naming failed for category %r", category_name)
        return {}


def refresh_clusters_for_category(
    db: Session,
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    category_name: str = "",
    llm_provider=None,
) -> int:
    """Recompute keyword clusters for one category. Returns number of clusters found."""
    starred = db.execute(
        select(NewsItem.id, NewsItem.embedding, NewsItem.extracted_keywords)
        .join(news_item_categories, news_item_categories.c.news_item_id == NewsItem.id)
        .where(
            news_item_categories.c.category_id == category_id,
            NewsItem.user_id == user_id,
            NewsItem.is_relevant == True,  # noqa: E712
            NewsItem.embedding.isnot(None),
            NewsItem.extracted_keywords.isnot(None),
        )
    ).all()

    if len(starred) < MIN_STARRED:
        return 0

    embeddings = [list(row.embedding) for row in starred]
    all_kws = [
        [normalize_keyword(k) for k in (row.extracted_keywords or []) if normalize_keyword(k)]
        for row in starred
    ]

    labels = _cluster_articles(embeddings)
    n_clusters = max(labels) + 1 if labels else 0
    top_kws = _tfidf_keywords(labels, all_kws, n_clusters)

    # Generate human-readable labels via LLM
    llm_labels: dict[int, str] = {}
    if llm_provider is not None and category_name:
        llm_labels = _generate_cluster_labels(category_name, top_kws, llm_provider)

    # Replace existing clusters for this category
    db.execute(
        delete(KeywordCluster).where(
            KeywordCluster.user_id == user_id,
            KeywordCluster.category_id == category_id,
        )
    )

    cluster_sizes = defaultdict(int)
    for label in labels:
        cluster_sizes[label] += 1

    rows = []
    for ci, keywords in top_kws.items():
        size = cluster_sizes.get(ci, 0)
        # LLM label if available, else fall back to top TF-IDF keyword
        label = llm_labels.get(ci) or (keywords[0][0] if keywords else "")
        for kw, score in keywords:
            rows.append(KeywordCluster(
                id=uuid.uuid4(),
                user_id=user_id,
                category_id=category_id,
                cluster_index=ci,
                cluster_label=label,
                keyword=kw,
                score=score,
                cluster_size=size,
            ))
    if rows:
        db.add_all(rows)

    return n_clusters


def refresh_clusters_for_user(db: Session, user_id: uuid.UUID) -> None:
    """Recompute keyword clusters for all active categories of a user."""
    from app.services.llm.factory import get_llm_provider
    try:
        llm_provider = get_llm_provider()
    except Exception:
        logger.warning("Could not load LLM provider for cluster naming — labels will use top keyword")
        llm_provider = None

    categories = db.scalars(
        select(Category).where(Category.user_id == user_id, Category.is_active == True)  # noqa: E712
    ).all()

    total_clusters = 0
    for cat in categories:
        try:
            n = refresh_clusters_for_category(
                db, user_id, cat.id,
                category_name=cat.name,
                llm_provider=llm_provider,
            )
            total_clusters += n
        except Exception:
            logger.exception("Cluster refresh failed for category %s", cat.id)

    db.commit()
    logger.info("Keyword cluster refresh for user %s: %d clusters across %d categories", user_id, total_clusters, len(categories))
