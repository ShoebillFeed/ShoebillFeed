import uuid
from datetime import datetime, timedelta, timezone

from app.models.category import Category
from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.source import Source


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_category(db_session, user_id, name="Tech", color="#6366f1"):
    cat = Category(user_id=user_id, name=name, color=color, keywords=[])
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_item(db_session, source, user_id, *, keywords=None, categories=None, fetched_at=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        extracted_keywords=keywords,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
    if categories:
        item.categories = categories
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, sources, *, keywords=None, categories=None, created_at=None):
    cluster = NewsCluster(user_id=user_id, title="Cluster", extracted_keywords=keywords)
    if categories:
        cluster.categories = categories
    if created_at:
        cluster.created_at = created_at
    db_session.add(cluster)
    db_session.flush()
    for source in sources:
        db_session.add(NewsItem(
            source_id=source.id, user_id=user_id, cluster_id=cluster.id,
            title="member", url=f"https://example.com/{uuid.uuid4().hex}", url_hash=f"hash-{uuid.uuid4().hex}",
        ))
    db_session.flush()
    return cluster


def _post(client, **body):
    return client.post("/api/stats/keyword-trend", json=body)


class TestKeywordTrend:
    def test_requires_auth(self, client):
        resp = client.post(
            "/api/stats/keyword-trend", json={"topics": [{"label": "AI", "keywords": ["ai"]}]}
        )
        assert resp.status_code == 401

    def test_counts_a_matching_news_item(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, keywords=["ai", "chips"])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "AI", "keywords": ["ai"]}])
        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["label"] == "AI"
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_counts_a_matching_news_cluster_once_not_per_member(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        _make_cluster(db_session, user.id, [source_a, source_b], keywords=["election"])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "Politics", "keywords": ["election"]}])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_is_case_insensitive(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, keywords=["Artificial Intelligence"])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "AI", "keywords": ["artificial intelligence"]}])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_or_matches_any_keyword_in_the_topic(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, keywords=["llm"])
        _make_item(db_session, source, user.id, keywords=["chatbot"])
        _make_item(db_session, source, user.id, keywords=["unrelated"])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "AI", "keywords": ["llm", "chatbot"]}])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 2

    def test_multiple_topics_are_counted_independently(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, keywords=["ai"])
        _make_item(db_session, source, user.id, keywords=["ai"])
        _make_item(db_session, source, user.id, keywords=["crypto"])
        db_session.commit()

        resp = _post(
            auth_client,
            topics=[{"label": "AI", "keywords": ["ai"]}, {"label": "Crypto", "keywords": ["crypto"]}],
        )
        body = resp.json()
        by_label = {t["label"]: sum(p["count"] for p in t["points"]) for t in body}
        assert by_label == {"AI": 2, "Crypto": 1}

    def test_filters_by_category(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        tech = _make_category(db_session, user.id, name="Tech")
        world = _make_category(db_session, user.id, name="World")
        _make_item(db_session, source, user.id, keywords=["ai"], categories=[tech])
        _make_item(db_session, source, user.id, keywords=["ai"], categories=[world])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "AI", "keywords": ["ai"]}], category_ids=[str(tech.id)])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_filters_by_source(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        _make_item(db_session, source_a, user.id, keywords=["ai"])
        _make_item(db_session, source_b, user.id, keywords=["ai"])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "AI", "keywords": ["ai"]}], source_ids=[str(source_a.id)])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_cluster_source_filter_matches_any_member_source(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="A")
        source_b = _make_source(db_session, user.id, name="B")
        _make_cluster(db_session, user.id, [source_a, source_b], keywords=["election"])
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "P", "keywords": ["election"]}], source_ids=[str(source_b.id)])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_excludes_items_outside_the_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, keywords=["ai"], fetched_at=now - timedelta(days=100))
        _make_item(db_session, source, user.id, keywords=["ai"], fetched_at=now - timedelta(days=1))
        db_session.commit()

        resp = _post(auth_client, topics=[{"label": "AI", "keywords": ["ai"]}], days=30)
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 1

    def test_does_not_count_another_users_items(self, client, db_session, make_user):
        from app.services.auth import create_token

        owner = make_user(username="owner")
        other = make_user(username="other")
        source = _make_source(db_session, owner.id)
        _make_item(db_session, source, owner.id, keywords=["ai"])
        db_session.commit()

        client.cookies.set("access_token", create_token(other.id, other.username))
        resp = _post(client, topics=[{"label": "AI", "keywords": ["ai"]}])
        body = resp.json()
        assert sum(p["count"] for p in body[0]["points"]) == 0

    def test_empty_keywords_after_stripping_returns_no_points_without_error(self, auth_client):
        resp = _post(auth_client, topics=[{"label": "Empty", "keywords": ["   "]}])
        assert resp.status_code == 200
        assert resp.json() == [{"label": "Empty", "points": []}]

    def test_rejects_more_than_six_topics(self, auth_client):
        topics = [{"label": f"T{i}", "keywords": ["x"]} for i in range(7)]
        resp = _post(auth_client, topics=topics)
        assert resp.status_code == 422

    def test_rejects_a_topic_with_no_keywords(self, auth_client):
        resp = _post(auth_client, topics=[{"label": "Empty", "keywords": []}])
        assert resp.status_code == 422
