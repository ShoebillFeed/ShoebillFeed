import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.models.category import Category
from app.models.news_item import NewsItem
from app.models.news_cluster import NewsCluster
from app.models.podcast_show import PodcastShow
from app.models.source import Source
from app.services.llm.base import PodcastScriptResult, PodcastScriptTurn
from app.services.podcast_script import (
    estimate_story_count,
    select_episode_items,
    build_script,
    build_episode_records,
    _story_payload,
)
from app.services.tts.audio_assembly import SILENCE_GAP_SECONDS


def _make_source(db_session, user_id, name="Feed"):
    source = Source(user_id=user_id, name=name, source_type="rss", config={"url": "https://example.com/feed"})
    db_session.add(source)
    db_session.flush()
    return source


def _make_category(db_session, user_id, name="Tech"):
    cat = Category(user_id=user_id, name=name, keywords=[])
    db_session.add(cat)
    db_session.flush()
    return cat


def _make_item(db_session, source, user_id, *, title="An article", published_at=None, categories=None, abstract=None):
    unique = uuid.uuid4().hex
    item = NewsItem(
        source_id=source.id,
        user_id=user_id,
        title=title,
        url=f"https://example.com/{unique}",
        url_hash=f"hash-{unique}",
        published_at=published_at,
        abstract=abstract,
    )
    if categories:
        item.categories = categories
    db_session.add(item)
    db_session.flush()
    return item


def _make_show(db_session, user_id, **overrides):
    defaults = dict(
        user_id=user_id,
        name="Morning Briefing",
        hosts=[{"id": "h1", "name": "Alex", "character_prompt": "curious", "voice": "en_US-libritts_r-medium#0"}],
        category_ids=[],
        source_ids=[],
        time_window_hours=24,
        target_length_minutes=10,
        language="en",
    )
    defaults.update(overrides)
    show = PodcastShow(**defaults)
    db_session.add(show)
    db_session.flush()
    return show


class TestEstimateStoryCount:
    def test_scales_with_target_minutes(self):
        assert estimate_story_count(5, 2) < estimate_story_count(15, 2)

    def test_never_below_one(self):
        assert estimate_story_count(1, 3) >= 1

    def test_capped_at_fifteen_regardless_of_length(self):
        assert estimate_story_count(15, 1) <= 15

    def test_more_hosts_leaves_room_for_fewer_stories_at_fixed_length(self):
        # More hosts means more conversational back-and-forth per story, so
        # the same word budget fits fewer distinct stories.
        assert estimate_story_count(10, 3) <= estimate_story_count(10, 1)

    def test_explicit_words_per_minute_overrides_the_settings_default(self):
        # A slower engine (e.g. Chatterbox) should fit fewer stories into the
        # same target length than the Piper-calibrated default would.
        assert estimate_story_count(10, 1, words_per_minute=80) <= estimate_story_count(10, 1, words_per_minute=210)

    def test_falls_back_to_the_configured_setting_when_not_given_explicitly(self, monkeypatch):
        from app.config import get_settings

        monkeypatch.setattr(get_settings(), "podcast_words_per_minute", 80)
        assert estimate_story_count(10, 1) == estimate_story_count(10, 1, words_per_minute=80)


class TestSelectEpisodeItems:
    def test_filters_out_items_outside_time_window(self, db_session, make_user):
        user = make_user()
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, title="Fresh", published_at=now - timedelta(hours=1))
        _make_item(db_session, source, user.id, title="Stale", published_at=now - timedelta(hours=48))
        db_session.commit()
        show = _make_show(db_session, user.id, time_window_hours=24)
        db_session.commit()

        items = select_episode_items(db_session, show)

        titles = {i.title for i in items}
        assert "Fresh" in titles
        assert "Stale" not in titles

    def test_filters_by_show_category_ids(self, db_session, make_user):
        user = make_user()
        source = _make_source(db_session, user.id)
        cat_a = _make_category(db_session, user.id, "A")
        cat_b = _make_category(db_session, user.id, "B")
        now = datetime.now(timezone.utc)
        _make_item(db_session, source, user.id, title="In A", published_at=now, categories=[cat_a])
        _make_item(db_session, source, user.id, title="In B", published_at=now, categories=[cat_b])
        db_session.commit()
        show = _make_show(db_session, user.id, category_ids=[cat_a.id])
        db_session.commit()

        items = select_episode_items(db_session, show)

        titles = {i.title for i in items}
        assert "In A" in titles
        assert "In B" not in titles

    def test_filters_by_show_source_ids(self, db_session, make_user):
        user = make_user()
        source_a = _make_source(db_session, user.id, "Source A")
        source_b = _make_source(db_session, user.id, "Source B")
        now = datetime.now(timezone.utc)
        _make_item(db_session, source_a, user.id, title="From A", published_at=now)
        _make_item(db_session, source_b, user.id, title="From B", published_at=now)
        db_session.commit()
        show = _make_show(db_session, user.id, source_ids=[source_a.id])
        db_session.commit()

        items = select_episode_items(db_session, show)

        titles = {i.title for i in items}
        assert "From A" in titles
        assert "From B" not in titles

    def test_caps_item_count_by_target_length_not_by_window(self, db_session, make_user):
        user = make_user()
        source = _make_source(db_session, user.id)
        now = datetime.now(timezone.utc)
        for i in range(20):
            _make_item(db_session, source, user.id, title=f"Item {i}", published_at=now - timedelta(minutes=i))
        db_session.commit()
        # 1 minute / 1 host -> estimate_story_count caps well below the 20 available.
        show = _make_show(db_session, user.id, target_length_minutes=1, time_window_hours=48)
        db_session.commit()

        items = select_episode_items(db_session, show)

        assert len(items) == estimate_story_count(1, 1)
        assert len(items) < 20


class TestStoryPayload:
    def test_news_item_payload_uses_abstract_and_source_name(self, db_session, make_user):
        user = make_user()
        source = _make_source(db_session, user.id, "The Daily")
        item = _make_item(db_session, source, user.id, title="Big News", abstract="Something happened.")
        db_session.commit()

        payload = _story_payload(item)

        assert payload == {
            "title": "Big News", "content": "Something happened.", "source_name": "The Daily", "url": item.url,
        }

    def test_news_item_payload_falls_back_to_title_when_no_abstract(self, db_session, make_user):
        user = make_user()
        source = _make_source(db_session, user.id)
        item = _make_item(db_session, source, user.id, title="Headline Only")
        db_session.commit()

        payload = _story_payload(item)

        assert payload["content"] == "Headline Only"

    def test_cluster_payload_lists_all_member_source_names(self, db_session, make_user):
        user = make_user()
        source_a = _make_source(db_session, user.id, "Source A")
        source_b = _make_source(db_session, user.id, "Source B")
        cluster = NewsCluster(user_id=user.id, title="Big Event", unified_abstract="It happened everywhere.")
        db_session.add(cluster)
        db_session.flush()
        db_session.add(NewsItem(
            source_id=source_a.id, user_id=user.id, cluster_id=cluster.id,
            title="A's take", url="https://a.example/1", url_hash="hash-a",
        ))
        db_session.add(NewsItem(
            source_id=source_b.id, user_id=user.id, cluster_id=cluster.id,
            title="B's take", url="https://b.example/1", url_hash="hash-b",
        ))
        db_session.commit()
        db_session.refresh(cluster)

        payload = _story_payload(cluster)

        assert payload["title"] == "Big Event"
        assert payload["content"] == "It happened everywhere."
        assert "Source A" in payload["source_name"]
        assert "Source B" in payload["source_name"]


class TestBuildScript:
    def test_passes_hosts_and_serialized_stories_to_the_llm_provider(self, db_session, make_user):
        user = make_user()
        source = _make_source(db_session, user.id, "The Daily")
        item = _make_item(db_session, source, user.id, title="Big News", abstract="Something happened.")
        db_session.commit()
        show = _make_show(db_session, user.id, hosts=[
            {"id": "h1", "name": "Alex", "character_prompt": "curious", "voice": "v1"},
            {"id": "h2", "name": "Sam", "character_prompt": "dry", "voice": "v2"},
        ], target_length_minutes=7, language="de")
        db_session.commit()

        fake_result = PodcastScriptResult(turns=[PodcastScriptTurn(host_id="h1", text="Hello!")])
        fake_provider = MagicMock()
        fake_provider.generate_podcast_script.return_value = fake_result

        with patch("app.services.podcast_script.get_llm_provider", return_value=fake_provider):
            result = build_script(show, [item])

        assert result is fake_result
        kwargs = fake_provider.generate_podcast_script.call_args.kwargs
        assert [h["id"] for h in kwargs["hosts"]] == ["h1", "h2"]
        assert kwargs["target_minutes"] == 7
        assert kwargs["language"] == "de"
        assert kwargs["stories"] == [
            {"title": "Big News", "content": "Something happened.", "source_name": "The Daily", "url": item.url},
        ]
        assert kwargs["show_description"] == show.description
        assert kwargs["words_per_minute"] == 210  # Settings.podcast_words_per_minute default

    def test_passes_a_configured_non_default_words_per_minute(self, db_session, make_user, monkeypatch):
        # Kokoro/Chatterbox deployments tune this away from the
        # Piper-calibrated default -- build_script must actually use it.
        from app.config import get_settings

        monkeypatch.setattr(get_settings(), "podcast_words_per_minute", 150)

        user = make_user()
        source = _make_source(db_session, user.id, "The Daily")
        item = _make_item(db_session, source, user.id, title="Big News", abstract="Something happened.")
        db_session.commit()
        show = _make_show(db_session, user.id, hosts=[
            {"id": "h1", "name": "Alex", "character_prompt": "curious", "voice": "v1"},
        ], target_length_minutes=7, language="en")
        db_session.commit()

        fake_provider = MagicMock()
        fake_provider.generate_podcast_script.return_value = PodcastScriptResult(
            turns=[PodcastScriptTurn(host_id="h1", text="Hello!")]
        )

        with patch("app.services.podcast_script.get_llm_provider", return_value=fake_provider):
            build_script(show, [item])

        kwargs = fake_provider.generate_podcast_script.call_args.kwargs
        assert kwargs["words_per_minute"] == 150


class TestBuildEpisodeRecords:
    HOST_1 = {"id": "h1", "name": "Alex", "voice": "v1"}
    HOST_2 = {"id": "h2", "name": "Sam", "voice": "v2"}
    STORIES = [
        {"title": "Story A", "source_name": "Source A", "url": "https://a.example/1"},
        {"title": "Story B", "source_name": "Source B", "url": "https://b.example/1"},
    ]

    def test_script_entries_carry_resolved_host_names(self):
        turns = [(PodcastScriptTurn(host_id="h1", text="Hi!", story_index=None), self.HOST_1, 5.0)]
        script_entries, _ = build_episode_records(turns, self.STORIES)
        assert script_entries == [{"host_id": "h1", "host_name": "Alex", "story_index": None, "text": "Hi!"}]

    def test_shownote_recorded_at_first_mention_of_each_story(self):
        turns = [
            (PodcastScriptTurn(host_id="h1", text="Welcome!", story_index=None), self.HOST_1, 10.0),
            (PodcastScriptTurn(host_id="h2", text="Story A intro", story_index=0), self.HOST_2, 10.0),
            (PodcastScriptTurn(host_id="h1", text="More on A", story_index=0), self.HOST_1, 10.0),
            (PodcastScriptTurn(host_id="h2", text="Story B intro", story_index=1), self.HOST_2, 10.0),
        ]
        _, shownotes = build_episode_records(turns, self.STORIES)

        assert [n["title"] for n in shownotes] == ["Story A", "Story B"]
        # turn 0 (welcome, no gap yet) runs 0->10; turn 1 starts after one
        # SILENCE_GAP_SECONDS gap at 10 + gap; turn 3 (story B) starts after
        # three turns' audio plus three gaps.
        assert shownotes[0]["start_seconds"] == round(10.0 + SILENCE_GAP_SECONDS, 1)
        assert shownotes[1]["start_seconds"] == round(30.0 + 3 * SILENCE_GAP_SECONDS, 1)
        assert shownotes[0]["url"] == "https://a.example/1"

    def test_no_shownote_for_turns_without_a_story_index(self):
        turns = [(PodcastScriptTurn(host_id="h1", text="Just banter", story_index=None), self.HOST_1, 5.0)]
        _, shownotes = build_episode_records(turns, self.STORIES)
        assert shownotes == []

    def test_no_duplicate_shownote_for_repeated_story_index(self):
        turns = [
            (PodcastScriptTurn(host_id="h1", text="A part 1", story_index=0), self.HOST_1, 5.0),
            (PodcastScriptTurn(host_id="h2", text="A part 2", story_index=0), self.HOST_2, 5.0),
        ]
        _, shownotes = build_episode_records(turns, self.STORIES)
        assert len(shownotes) == 1

    def test_out_of_range_story_index_produces_no_shownote(self):
        turns = [(PodcastScriptTurn(host_id="h1", text="Ghost story", story_index=9), self.HOST_1, 5.0)]
        _, shownotes = build_episode_records(turns, self.STORIES)
        assert shownotes == []
