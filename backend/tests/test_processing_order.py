"""Processing order is LIFO: newest first.

When the process queue is backed up -- and it is serialized, concurrency 1,
because Ollama runs on one GPU -- the order items are selected and enqueued
in decides what actually reaches the feed. These pin that order so a later
refactor can't quietly drop it back to the arbitrary ordering a LIMIT with
no ORDER BY produced.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models import NewsCluster, NewsItem, Source
from app.tasks.process_tasks import unprocessed_cluster_ids, unprocessed_item_ids


@pytest.fixture
def source(db_session, make_user):
    user = make_user()
    src = Source(id=uuid.uuid4(), user_id=user.id, name="Feed", source_type="rss",
                 config={"url": "https://example.com/feed"}, is_active=True)
    db_session.add(src)
    db_session.flush()
    return src


def _item(db, source, *, minutes_ago: int, processed: bool = False, cluster_id=None):
    item = NewsItem(
        id=uuid.uuid4(), user_id=source.user_id, source_id=source.id,
        title=f"item-{minutes_ago}", url=f"https://example.com/{uuid.uuid4()}",
        url_hash=uuid.uuid4().hex, llm_processed=processed, cluster_id=cluster_id,
        fetched_at=datetime.now(tz=timezone.utc) - timedelta(minutes=minutes_ago),
    )
    db.add(item)
    db.flush()
    return item


class TestUnprocessedItemIds:
    def test_returns_newest_first(self, db_session, source):
        old = _item(db_session, source, minutes_ago=90)
        newest = _item(db_session, source, minutes_ago=1)
        middle = _item(db_session, source, minutes_ago=30)

        got = unprocessed_item_ids(db_session, source.user_id, 10)
        assert got == [newest.id, middle.id, old.id]

    def test_limit_keeps_the_newest_not_an_arbitrary_slice(self, db_session, source):
        # The whole point of the ordering: a backlog larger than the limit
        # must surface the freshest items, not whatever the plan returned.
        _item(db_session, source, minutes_ago=500)
        _item(db_session, source, minutes_ago=400)
        newest = _item(db_session, source, minutes_ago=2)

        assert unprocessed_item_ids(db_session, source.user_id, 1) == [newest.id]

    def test_skips_already_processed_items(self, db_session, source):
        _item(db_session, source, minutes_ago=1, processed=True)
        pending = _item(db_session, source, minutes_ago=60)

        assert unprocessed_item_ids(db_session, source.user_id, 10) == [pending.id]

    def test_skips_clustered_items(self, db_session, source):
        # Clustered items are processed via their cluster, not individually.
        cluster = NewsCluster(id=uuid.uuid4(), user_id=source.user_id, llm_processed=False)
        db_session.add(cluster)
        db_session.flush()
        _item(db_session, source, minutes_ago=1, cluster_id=cluster.id)
        standalone = _item(db_session, source, minutes_ago=60)

        assert unprocessed_item_ids(db_session, source.user_id, 10) == [standalone.id]

    def test_scopes_to_the_requested_user(self, db_session, source, make_user):
        other = make_user(username="bob")
        other_src = Source(id=uuid.uuid4(), user_id=other.id, name="Other", source_type="rss",
                           config={"url": "https://other.example/feed"}, is_active=True)
        db_session.add(other_src)
        db_session.flush()
        _item(db_session, other_src, minutes_ago=1)
        mine = _item(db_session, source, minutes_ago=60)

        assert unprocessed_item_ids(db_session, source.user_id, 10) == [mine.id]


class TestUnprocessedClusterIds:
    def _cluster(self, db, user_id, *, minutes_ago, processed=False):
        c = NewsCluster(
            id=uuid.uuid4(), user_id=user_id, llm_processed=processed,
            created_at=datetime.now(tz=timezone.utc) - timedelta(minutes=minutes_ago),
        )
        db.add(c)
        db.flush()
        return c

    def test_returns_newest_first(self, db_session, source):
        old = self._cluster(db_session, source.user_id, minutes_ago=120)
        newest = self._cluster(db_session, source.user_id, minutes_ago=3)

        assert unprocessed_cluster_ids(db_session, source.user_id, 10) == [newest.id, old.id]

    def test_skips_already_processed_clusters(self, db_session, source):
        self._cluster(db_session, source.user_id, minutes_ago=1, processed=True)
        pending = self._cluster(db_session, source.user_id, minutes_ago=60)

        assert unprocessed_cluster_ids(db_session, source.user_id, 10) == [pending.id]
