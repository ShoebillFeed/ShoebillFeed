import uuid
from datetime import datetime, timedelta, timezone

from app.models.podcast_episode import PodcastEpisode
from app.models.podcast_show import PodcastShow

VALID_HOST = {"id": "h1", "name": "Alex", "character_prompt": "Curious and upbeat", "voice": "en_US-libritts_r-medium#0"}


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


def _make_episode(db_session, show, user_id, *, status="ready", item_ids=None, cluster_ids=None,
                   duration_seconds=None, created_at=None):
    episode = PodcastEpisode(
        show_id=show.id, user_id=user_id, status=status,
        news_item_ids=item_ids or [], news_cluster_ids=cluster_ids or [],
        duration_seconds=duration_seconds,
        created_at=created_at or datetime.now(timezone.utc),
    )
    db_session.add(episode)
    db_session.flush()
    return episode


def _get(client, show_id, **params):
    return client.get("/api/stats/podcast-episode-trend", params={"show_id": str(show_id), **params})


class TestPodcastEpisodeTrend:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/podcast-episode-trend", params={"show_id": str(uuid.uuid4())})
        assert resp.status_code == 401

    def test_404_for_unknown_show(self, auth_client):
        resp = _get(auth_client, uuid.uuid4())
        assert resp.status_code == 404

    def test_404_for_another_users_show(self, client, db_session, make_user):
        from app.services.auth import create_token

        owner = make_user(username="owner")
        other = make_user(username="other")
        show = _make_show(db_session, owner.id)
        db_session.commit()

        client.cookies.set("access_token", create_token(other.id, other.username))
        resp = _get(client, show.id)
        assert resp.status_code == 404

    def test_returns_target_and_episode_stats(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id, target_length_minutes=12)
        _make_episode(
            db_session, show, user.id, duration_seconds=600,
            item_ids=[uuid.uuid4(), uuid.uuid4()], cluster_ids=[uuid.uuid4()],
        )
        db_session.commit()

        resp = _get(auth_client, show.id)
        assert resp.status_code == 200
        body = resp.json()
        assert body["target_minutes"] == 12
        assert len(body["episodes"]) == 1
        ep = body["episodes"][0]
        assert ep["actual_minutes"] == 10.0
        assert ep["story_count"] == 3

    def test_excludes_non_ready_episodes(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        _make_episode(db_session, show, user.id, status="pending")
        _make_episode(db_session, show, user.id, status="failed")
        db_session.commit()

        body = _get(auth_client, show.id).json()
        assert body["episodes"] == []

    def test_orders_oldest_to_newest(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        now = datetime.now(timezone.utc)
        newer = _make_episode(db_session, show, user.id, duration_seconds=300, created_at=now)
        older = _make_episode(db_session, show, user.id, duration_seconds=300, created_at=now - timedelta(days=1))
        db_session.commit()

        body = _get(auth_client, show.id).json()
        ids = [ep["id"] for ep in body["episodes"]]
        assert ids == [str(older.id), str(newer.id)]

    def test_respects_limit(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        for _ in range(5):
            _make_episode(db_session, show, user.id, duration_seconds=300)
        db_session.commit()

        body = _get(auth_client, show.id, limit=2).json()
        assert len(body["episodes"]) == 2

    def test_treats_missing_duration_as_zero(self, auth_client, db_session):
        user = auth_client.current_user
        show = _make_show(db_session, user.id)
        _make_episode(db_session, show, user.id, duration_seconds=None)
        db_session.commit()

        body = _get(auth_client, show.id).json()
        assert body["episodes"][0]["actual_minutes"] == 0.0
