import uuid
from datetime import datetime, timedelta, timezone

from app.models.category import Category
from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.podcast_episode import PodcastEpisode
from app.models.podcast_show import PodcastShow
from app.models.source import Source

VALID_HOST = {"id": "h1", "name": "Alex", "character_prompt": "Curious and upbeat", "voice": "en_US-libritts_r-medium#0"}


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


def _make_item(db_session, source, user_id, *, categories=None, keywords=None, title="An article"):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=title,
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        extracted_keywords=keywords,
    )
    if categories:
        item.categories = categories
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, sources, *, categories=None, keywords=None, title="Big story"):
    cluster = NewsCluster(user_id=user_id, title=title, extracted_keywords=keywords)
    if categories:
        cluster.categories = categories
    db_session.add(cluster)
    db_session.flush()
    for i, source in enumerate(sources):
        db_session.add(NewsItem(
            source_id=source.id, user_id=user_id, cluster_id=cluster.id,
            title=f"{title} ({i})", url=f"https://example.com/{uuid.uuid4().hex}", url_hash=f"hash-{uuid.uuid4().hex}",
        ))
    db_session.flush()
    db_session.refresh(cluster)
    return cluster


def _make_show(db_session, user_id, **overrides):
    defaults = dict(
        user_id=user_id, name="Morning Briefing", hosts=[VALID_HOST],
        category_ids=[], source_ids=[], time_window_hours=24,
        target_length_minutes=10, language="en",
    )
    defaults.update(overrides)
    show = PodcastShow(**defaults)
    db_session.add(show)
    db_session.flush()
    return show


def _make_episode(db_session, show, user_id, *, status="ready", item_ids=None, cluster_ids=None, created_at=None):
    episode = PodcastEpisode(
        show_id=show.id, user_id=user_id, status=status,
        news_item_ids=item_ids or [], news_cluster_ids=cluster_ids or [],
        created_at=created_at or datetime.now(timezone.utc),
    )
    db_session.add(episode)
    db_session.flush()
    return episode


class TestPodcastEpisodeStats:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/podcast-episodes", params={"show_id": str(uuid.uuid4())})
        assert resp.status_code == 401

    def test_404_for_unknown_show(self, auth_client):
        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(uuid.uuid4())})
        assert resp.status_code == 404

    def test_404_for_another_users_show(self, client, db_session, make_user):
        from app.services.auth import create_token

        owner = make_user(username="owner")
        other = make_user(username="other")
        show = _make_show(db_session, owner.id)
        db_session.commit()

        client.cookies.set("access_token", create_token(other.id, other.username))
        resp = client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id)})
        assert resp.status_code == 404

    def test_tallies_categories_keywords_and_source_for_a_standalone_item_episode(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id, name="TechCrunch")
        tech = _make_category(db_session, user.id, name="Tech", color="#6366f1")
        show = _make_show(db_session, user.id)
        item = _make_item(db_session, source, user.id, categories=[tech], keywords=["ai", "chips"])
        episode = _make_episode(db_session, show, user.id, item_ids=[item.id])
        db_session.commit()

        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id)})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        ep = body[0]
        assert ep["id"] == str(episode.id)
        assert ep["total_stories"] == 1
        assert ep["categories"] == [{"id": str(tech.id), "name": "Tech", "color": "#6366f1", "count": 1}]
        assert {"keyword": "ai", "count": 1} in ep["top_keywords"]
        assert {"keyword": "chips", "count": 1} in ep["top_keywords"]
        assert ep["top_sources"] == [{"name": "TechCrunch", "count": 1}]

    def test_cluster_contributes_distinct_sources_not_one_per_member_item(self, auth_client, db_session):
        user = auth_client.current_user
        source_a = _make_source(db_session, user.id, name="Source A")
        source_b = _make_source(db_session, user.id, name="Source A")  # same name, different source row
        world = _make_category(db_session, user.id, name="World", color="#f59e0b")
        show = _make_show(db_session, user.id)
        cluster = _make_cluster(
            db_session, user.id, [source_a, source_b, source_a], categories=[world], keywords=["election"],
        )
        _make_episode(db_session, show, user.id, cluster_ids=[cluster.id])
        db_session.commit()

        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id)})
        body = resp.json()[0]
        # Three member items, but only one distinct source *name* -- should
        # count once, not three times.
        assert body["top_sources"] == [{"name": "Source A", "count": 1}]
        assert body["categories"][0]["name"] == "World"
        assert {"keyword": "election", "count": 1} in body["top_keywords"]

    def test_excludes_non_ready_episodes(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        show = _make_show(db_session, user.id)
        item = _make_item(db_session, source, user.id)
        _make_episode(db_session, show, user.id, status="pending", item_ids=[item.id])
        _make_episode(db_session, show, user.id, status="failed", item_ids=[item.id])
        _make_episode(db_session, show, user.id, status="generating", item_ids=[item.id])
        db_session.commit()

        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id)})
        assert resp.json() == []

    def test_orders_oldest_to_newest(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        now = datetime.now(timezone.utc)
        newer = _make_episode(db_session, show, user.id, created_at=now)
        older = _make_episode(db_session, show, user.id, created_at=now - timedelta(days=1))
        db_session.commit()

        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id)})
        ids = [e["id"] for e in resp.json()]
        assert ids == [str(older.id), str(newer.id)]

    def test_limit_caps_the_number_of_episodes_returned(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        for _ in range(5):
            _make_episode(db_session, show, user.id)
        db_session.commit()

        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id), "limit": 2})
        assert len(resp.json()) == 2

    def test_top_keywords_and_sources_capped_at_eight_sorted_by_count(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        source = _make_source(db_session, user.id, name="Only Source")

        # 10 distinct keywords total: "popular" repeated across 5 items, plus
        # 9 items each with their own unique keyword -- more than the top-8
        # cap, so this actually exercises truncation.
        item_ids = []
        for _ in range(5):
            item = _make_item(db_session, source, user.id, keywords=["popular"])
            item_ids.append(item.id)
        for i in range(9):
            item = _make_item(db_session, source, user.id, keywords=[f"kw{i}"])
            item_ids.append(item.id)
        _make_episode(db_session, show, user.id, item_ids=item_ids)
        db_session.commit()

        resp = auth_client.get("/api/stats/podcast-episodes", params={"show_id": str(show.id)})
        body = resp.json()[0]
        assert len(body["top_keywords"]) == 8
        assert body["top_keywords"][0] == {"keyword": "popular", "count": 5}
