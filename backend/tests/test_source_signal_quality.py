import uuid
from datetime import datetime, timedelta, timezone

from app.models.news_cluster import NewsCluster
from app.models.news_item import NewsItem
from app.models.source import Source


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": f"https://example.com/{name}"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_item(db_session, source, user_id, *, is_relevant=False, is_disliked=False, is_read=False,
                fetched_at=None, cluster_id=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=f"Article {unique}",
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        is_relevant=is_relevant,
        is_disliked=is_disliked,
        is_read=is_read,
        fetched_at=fetched_at or datetime.now(timezone.utc),
        cluster_id=cluster_id,
    )
    db_session.add(item)
    db_session.flush()
    return item


def _make_cluster(db_session, user_id, *, is_relevant=False, is_read=False):
    cluster = NewsCluster(user_id=user_id, title="Cluster", is_relevant=is_relevant, is_read=is_read)
    db_session.add(cluster)
    db_session.flush()
    return cluster


def _get(client, **params):
    return client.get("/api/stats/source-signal-quality", params=params)


def _by_name(resp):
    return {r["name"]: r for r in resp.json()}


class TestSourceSignalQuality:
    def test_requires_auth(self, client):
        resp = client.get("/api/stats/source-signal-quality")
        assert resp.status_code == 401

    def test_counts_relevant_disliked_read_per_source(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        _make_item(db_session, source, user.id, is_relevant=True, is_read=True)
        _make_item(db_session, source, user.id, is_disliked=True, is_read=True)
        _make_item(db_session, source, user.id)
        db_session.commit()

        resp = _get(auth_client)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        row = body[0]
        assert row["total"] == 3
        assert row["relevant"] == 1
        assert row["disliked"] == 1
        assert row["read"] == 2

    def test_separates_sources(self, auth_client, db_session):
        user = auth_client.current_user
        good = _make_source(db_session, user.id, name="Good")
        bad = _make_source(db_session, user.id, name="Bad")
        _make_item(db_session, good, user.id, is_relevant=True)
        _make_item(db_session, good, user.id, is_relevant=True)
        _make_item(db_session, bad, user.id, is_disliked=True)
        db_session.commit()

        resp = _get(auth_client)
        by_name = {r["name"]: r for r in resp.json()}
        assert by_name["Good"]["relevant"] == 2
        assert by_name["Good"]["disliked"] == 0
        assert by_name["Bad"]["disliked"] == 1

    def test_sorted_by_total_descending(self, auth_client, db_session):
        user = auth_client.current_user
        small = _make_source(db_session, user.id, name="Small")
        big = _make_source(db_session, user.id, name="Big")
        _make_item(db_session, small, user.id)
        for _ in range(3):
            _make_item(db_session, big, user.id)
        db_session.commit()

        resp = _get(auth_client)
        names = [r["name"] for r in resp.json()]
        assert names == ["Big", "Small"]

    def test_respects_day_window(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, fetched_at=now - timedelta(days=100))
        _make_item(db_session, source, user.id, fetched_at=now - timedelta(days=1))
        db_session.commit()

        resp = _get(auth_client, days=30)
        assert resp.json()[0]["total"] == 1

    def test_excludes_sources_with_no_items_in_window(self, auth_client, db_session):
        user = auth_client.current_user
        _make_source(db_session, user.id, name="Empty")
        db_session.commit()

        resp = _get(auth_client)
        assert resp.json() == []

    def test_does_not_count_another_users_items(self, auth_client, db_session, make_user):
        other = make_user(username="other")
        other_source = _make_source(db_session, other.id, name="OtherSource")
        _make_item(db_session, other_source, other.id, is_relevant=True)
        db_session.commit()

        resp = _get(auth_client)
        assert resp.json() == []


class TestSourceSignalQualityClusterCredit:
    def test_single_source_cluster_credits_the_full_relevant_verdict(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        cluster = _make_cluster(db_session, user.id, is_relevant=True)
        _make_item(db_session, source, user.id, cluster_id=cluster.id)
        _make_item(db_session, source, user.id, cluster_id=cluster.id)  # same source, 2nd member item
        db_session.commit()

        row = _by_name(_get(auth_client))["Feed"]
        assert row["total"] == 2
        # One distinct source in the cluster -> full 1.0 credit, not 2x for
        # having two member items from that same source.
        assert row["relevant"] == 1.0

    def test_multi_source_cluster_splits_credit_evenly(self, auth_client, db_session):
        user = auth_client.current_user
        a = _make_source(db_session, user.id, name="A")
        b = _make_source(db_session, user.id, name="B")
        cluster = _make_cluster(db_session, user.id, is_relevant=True)
        _make_item(db_session, a, user.id, cluster_id=cluster.id)
        _make_item(db_session, b, user.id, cluster_id=cluster.id)
        db_session.commit()

        by_name = _by_name(_get(auth_client))
        assert by_name["A"]["relevant"] == 0.5
        assert by_name["B"]["relevant"] == 0.5

    def test_one_upvote_always_sums_to_one_across_member_sources(self, auth_client, db_session):
        user = auth_client.current_user
        sources = [_make_source(db_session, user.id, name=f"S{i}") for i in range(4)]
        cluster = _make_cluster(db_session, user.id, is_relevant=True)
        for s in sources:
            _make_item(db_session, s, user.id, cluster_id=cluster.id)
        db_session.commit()

        by_name = _by_name(_get(auth_client))
        total_credit = sum(by_name[f"S{i}"]["relevant"] for i in range(4))
        assert total_credit == 1.0

    def test_a_not_yet_relevant_cluster_contributes_no_credit(self, auth_client, db_session):
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        cluster = _make_cluster(db_session, user.id, is_relevant=False)
        _make_item(db_session, source, user.id, cluster_id=cluster.id)
        db_session.commit()

        row = _by_name(_get(auth_client))["Feed"]
        assert row["relevant"] == 0

    def test_cluster_read_credit_splits_the_same_way(self, auth_client, db_session):
        user = auth_client.current_user
        a = _make_source(db_session, user.id, name="A")
        b = _make_source(db_session, user.id, name="B")
        cluster = _make_cluster(db_session, user.id, is_read=True)
        _make_item(db_session, a, user.id, cluster_id=cluster.id)
        _make_item(db_session, b, user.id, cluster_id=cluster.id)
        db_session.commit()

        by_name = _by_name(_get(auth_client))
        assert by_name["A"]["read"] == 0.5
        assert by_name["B"]["read"] == 0.5

    def test_a_cluster_can_never_contribute_dislike_credit(self, auth_client, db_session):
        # NewsCluster has no is_disliked concept at all -- dislike_cluster()
        # only ever sets is_read/is_relevant (api/clusters.py) -- so even a
        # cluster marked not-relevant (the closest thing to "disliked" a
        # cluster has) must never show up as a disliked count.
        user = auth_client.current_user
        source = _make_source(db_session, user.id)
        cluster = _make_cluster(db_session, user.id, is_relevant=False, is_read=True)
        _make_item(db_session, source, user.id, cluster_id=cluster.id)
        db_session.commit()

        row = _by_name(_get(auth_client))["Feed"]
        assert row["disliked"] == 0

    def test_standalone_and_clustered_credit_combine_for_the_same_source(self, auth_client, db_session):
        user = auth_client.current_user
        a = _make_source(db_session, user.id, name="A")
        b = _make_source(db_session, user.id, name="B")
        _make_item(db_session, a, user.id, is_relevant=True)  # standalone: full credit
        cluster = _make_cluster(db_session, user.id, is_relevant=True)
        _make_item(db_session, a, user.id, cluster_id=cluster.id)
        _make_item(db_session, b, user.id, cluster_id=cluster.id)
        db_session.commit()

        by_name = _by_name(_get(auth_client))
        assert by_name["A"]["relevant"] == 1.5  # 1.0 standalone + 0.5 from the cluster
        assert by_name["A"]["total"] == 2
        assert by_name["B"]["relevant"] == 0.5
        assert by_name["B"]["total"] == 1
