import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from xml.etree.ElementTree import fromstring

from PIL import Image

from app.models.podcast_episode import PodcastEpisode
from app.services.podcast_feed import render_rss_feed, episode_description, build_chapters_json

VALID_HOST = {"id": "h1", "name": "Alex", "character_prompt": "Curious and upbeat", "voice": "en_US-libritts_r-medium#0"}


def _show_payload(**overrides):
    payload = {
        "name": "Morning Briefing",
        "hosts": [VALID_HOST],
        "category_ids": [],
        "source_ids": [],
        "time_window_hours": 24,
        "target_length_minutes": 10,
        "language": "en",
        "schedule_time": "07:00",
        "timezone": "UTC",
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def _make_ready_episode(db_session, podcast_dirs, show, content=b"fake mp3 bytes", script=None, shownotes=None):
    episode = PodcastEpisode(
        show_id=show.id, user_id=show.user_id, status="ready", duration_seconds=300,
        script=script if script is not None else [{"host_id": "h1", "text": "Hello and welcome to the show."}],
        shownotes=shownotes,
        generated_at=datetime.now(timezone.utc),
    )
    db_session.add(episode)
    db_session.flush()
    rel_path = f"{show.user_id}/{episode.id}.mp3"
    abs_path = os.path.join(podcast_dirs.podcast_audio_dir, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)
    episode.audio_path = rel_path
    db_session.commit()
    return episode


# --- episode_description() ---------------------------------------------------

class TestEpisodeDescription:
    def test_shownotes_are_separated_by_a_blank_line(self):
        episode = PodcastEpisode(shownotes=[
            {"title": "Story A", "source_name": "Source A", "url": "https://a.example/1", "start_seconds": 0.0},
            {"title": "Story B", "source_name": "Source B", "url": "https://b.example/1", "start_seconds": 30.0},
        ])
        description = episode_description(episode)
        assert "Story A (Source A)\nhttps://a.example/1\n\nStory B (Source B)" in description

    def test_falls_back_to_one_paragraph_per_turn_without_shownotes(self):
        episode = PodcastEpisode(shownotes=None, script=[
            {"host_id": "h1", "text": "Welcome to the show!"},
            {"host_id": "h2", "text": "Great to be here."},
        ])
        description = episode_description(episode)
        assert description == "Welcome to the show!\n\nGreat to be here."

    def test_empty_without_script_or_shownotes(self):
        episode = PodcastEpisode(shownotes=None, script=None)
        assert episode_description(episode) == ""


# --- build_chapters_json() ---------------------------------------------------

class TestBuildChaptersJson:
    def test_maps_shownotes_to_podcast_namespace_chapters(self):
        episode = PodcastEpisode(shownotes=[
            {"title": "Story A", "source_name": "Source A", "url": "https://a.example/1", "start_seconds": 0.0},
            {"title": "Story B", "source_name": "Source B", "url": "https://b.example/1", "start_seconds": 42.5},
        ])
        result = build_chapters_json(episode)
        assert result["version"] == "1.2.0"
        assert result["chapters"] == [
            {"startTime": 0.0, "title": "Story A (Source A)", "url": "https://a.example/1"},
            {"startTime": 42.5, "title": "Story B (Source B)", "url": "https://b.example/1"},
        ]

    def test_omits_url_when_a_shownote_has_none(self):
        episode = PodcastEpisode(shownotes=[
            {"title": "Story A", "source_name": "Source A", "url": None, "start_seconds": 0.0},
        ])
        chapter = build_chapters_json(episode)["chapters"][0]
        assert "url" not in chapter

    def test_empty_chapters_list_without_shownotes(self):
        episode = PodcastEpisode(shownotes=None)
        assert build_chapters_json(episode) == {"version": "1.2.0", "chapters": []}


# --- render_rss_feed() -------------------------------------------------------

class TestRenderRssFeed:
    def test_produces_well_formed_xml_with_expected_item_fields(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()
        episode = _make_ready_episode(db_session, podcast_dirs, show)

        xml = render_rss_feed(show, [episode], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        assert root.tag == "rss"
        channel = root.find("channel")
        assert channel.find("title").text == "Morning Briefing"
        items = channel.findall("item")
        assert len(items) == 1
        item = items[0]
        assert item.find("guid").text == str(episode.id)
        assert item.find("guid").attrib["isPermaLink"] == "false"
        assert "Hello and welcome" in item.find("description").text
        enclosure = item.find("enclosure")
        assert enclosure.attrib["url"] == f"https://podcast.test/api/podcasts/public/tok123/episodes/{episode.id}/audio"
        assert enclosure.attrib["type"] == "audio/mpeg"
        assert int(enclosure.attrib["length"]) > 0
        duration = item.find("{http://www.itunes.com/dtds/podcast-1.0.dtd}duration")
        assert duration.text == "300"
        # No shownotes on this fixture -- no chapters tag to point at.
        assert item.find("{https://podcastindex.org/namespace/1.0}chapters") is None

    def test_includes_podcast_chapters_tag_when_shownotes_are_present(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()
        episode = _make_ready_episode(db_session, podcast_dirs, show, shownotes=[
            {"title": "Story A", "source_name": "Source A", "url": "https://a.example/1", "start_seconds": 0.0},
        ])

        xml = render_rss_feed(show, [episode], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        item = fromstring(xml).find("channel").find("item")
        chapters = item.find("{https://podcastindex.org/namespace/1.0}chapters")
        assert chapters is not None
        assert chapters.attrib["url"] == f"https://podcast.test/api/podcasts/public/tok123/episodes/{episode.id}/chapters.json"
        assert chapters.attrib["type"] == "application/json+chapters"

    def test_root_declares_the_podcast_namespace(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()

        xml = render_rss_feed(show, [], "https://podcast.test", podcast_dirs.podcast_audio_dir)
        assert 'xmlns:podcast="https://podcastindex.org/namespace/1.0"' in xml

    def test_no_episodes_yields_empty_item_list(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()

        xml = render_rss_feed(show, [], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        assert root.find("channel").findall("item") == []

    def test_channel_description_defaults_without_a_show_description(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()

        xml = render_rss_feed(show, [], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        assert "Morning Briefing" in root.find("channel").find("description").text

    def test_channel_description_uses_show_description_when_set(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(
            **_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True,
            description="Skeptical daily markets briefing.",
        )
        db_session.add(show)
        db_session.flush()

        xml = render_rss_feed(show, [], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        assert root.find("channel").find("description").text == "Skeptical daily markets briefing."

    def test_itunes_image_defaults_to_app_icon_without_a_cover(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()

        xml = render_rss_feed(show, [], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        image = root.find("channel").find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
        assert image.attrib["href"] == "https://podcast.test/icon-512.png"

    def test_itunes_image_uses_public_cover_route_when_set(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(
            **_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True,
            cover_image_path="covers/some-show.png",
        )
        db_session.add(show)
        db_session.flush()

        xml = render_rss_feed(show, [], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        image = root.find("channel").find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
        assert image.attrib["href"] == "https://podcast.test/api/podcasts/public/tok123/cover"

    def test_episode_description_lists_shownotes_with_sources_when_present(self, db_session, make_user, podcast_dirs):
        from app.models.podcast_show import PodcastShow

        user = make_user()
        show = PodcastShow(**_show_payload(), user_id=user.id, public_feed_token="tok123", public_feed_enabled=True)
        db_session.add(show)
        db_session.flush()
        episode = _make_ready_episode(db_session, podcast_dirs, show)
        episode.shownotes = [
            {"title": "Big Story", "source_name": "The Daily", "url": "https://example.com/1", "start_seconds": 12.0},
        ]
        db_session.commit()

        xml = render_rss_feed(show, [episode], "https://podcast.test", podcast_dirs.podcast_audio_dir)

        root = fromstring(xml)
        description = root.find("channel").find("item").find("description").text
        assert "Big Story" in description
        assert "The Daily" in description
        assert "https://example.com/1" in description


# --- Enable / disable / regenerate (authenticated) ---------------------------

def test_enable_generates_a_token_and_returns_a_url(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed")

    assert resp.status_code == 200
    body = resp.json()
    assert body["public_feed_enabled"] is True
    assert body["public_feed_url"].startswith(f"{public_base_url}/api/podcasts/public/")
    assert body["public_feed_url"].endswith("/feed.xml")
    token = body["public_feed_url"].split("/")[-2]
    assert len(token) > 20  # secrets.token_urlsafe(32) produces a long string


def test_enable_without_public_base_url_configured_returns_400(auth_client):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed")

    assert resp.status_code == 400


def test_disable_then_reenable_keeps_the_same_token(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    first = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()

    auth_client.delete(f"/api/podcasts/shows/{created['id']}/public-feed")
    second = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()

    assert first["public_feed_url"] == second["public_feed_url"]


def test_disable_clears_the_url_from_the_response(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed")

    resp = auth_client.delete(f"/api/podcasts/shows/{created['id']}/public-feed")

    assert resp.status_code == 200
    body = resp.json()
    assert body["public_feed_enabled"] is False
    assert body["public_feed_url"] is None


def test_regenerate_issues_a_different_token(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    first = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()

    resp = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed/regenerate")

    assert resp.status_code == 200
    second = resp.json()
    assert second["public_feed_url"] != first["public_feed_url"]


def test_regenerate_before_enabling_returns_400(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed/regenerate")

    assert resp.status_code == 400


def test_user_cannot_toggle_another_users_show_feed(client, make_user, public_base_url):
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")
    client.cookies.set("access_token", create_token(user1.id, user1.username))
    created = client.post("/api/podcasts/shows", json=_show_payload()).json()

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    assert client.post(f"/api/podcasts/shows/{created['id']}/public-feed").status_code == 404
    assert client.delete(f"/api/podcasts/shows/{created['id']}/public-feed").status_code == 404
    assert client.post(f"/api/podcasts/shows/{created['id']}/public-feed/regenerate").status_code == 404


# --- Public feed.xml route (unauthenticated) ---------------------------------

def test_public_feed_returns_xml_for_valid_enabled_token(auth_client, public_base_url, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    _make_ready_episode(db_session, podcast_dirs, show)
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()  # podcast apps never send auth cookies
    resp = auth_client.get(f"/api/podcasts/public/{token}/feed.xml")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/rss+xml")
    root = fromstring(resp.content)
    assert len(root.find("channel").findall("item")) == 1


def test_public_feed_only_includes_ready_episodes(auth_client, public_base_url, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    _make_ready_episode(db_session, podcast_dirs, show)
    db_session.add(PodcastEpisode(show_id=show.id, user_id=show.user_id, status="pending"))
    db_session.add(PodcastEpisode(show_id=show.id, user_id=show.user_id, status="failed"))
    db_session.commit()
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/feed.xml")

    root = fromstring(resp.content)
    assert len(root.find("channel").findall("item")) == 1


def test_public_feed_404s_when_disabled(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    token = enabled["public_feed_url"].split("/")[-2]
    auth_client.delete(f"/api/podcasts/shows/{created['id']}/public-feed")

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/feed.xml")

    assert resp.status_code == 404


def test_public_feed_404s_for_unknown_token(client):
    resp = client.get("/api/podcasts/public/not-a-real-token/feed.xml")
    assert resp.status_code == 404


# --- Public episode audio route (unauthenticated) -----------------------------

def test_public_audio_streams_for_valid_token_and_matching_episode(auth_client, public_base_url, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    content = b"0123456789" * 100
    episode = _make_ready_episode(db_session, podcast_dirs, show, content=content)
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/episodes/{episode.id}/audio")
    assert resp.status_code == 200
    assert resp.content == content

    range_resp = auth_client.get(
        f"/api/podcasts/public/{token}/episodes/{episode.id}/audio", headers={"Range": "bytes=10-19"}
    )
    assert range_resp.status_code == 206
    assert range_resp.content == content[10:20]


def test_public_audio_404s_for_episode_belonging_to_a_different_show(auth_client, public_base_url, db_session, podcast_dirs):
    """The critical cross-show scoping check: a valid token for show A must
    not grant access to show B's episode audio, even with a guessed/known id."""
    from app.models.podcast_show import PodcastShow

    show_a = auth_client.post("/api/podcasts/shows", json=_show_payload(name="Show A")).json()
    show_b = auth_client.post("/api/podcasts/shows", json=_show_payload(name="Show B")).json()
    enabled_a = auth_client.post(f"/api/podcasts/shows/{show_a['id']}/public-feed").json()
    show_b_orm = db_session.get(PodcastShow, uuid.UUID(show_b["id"]))
    other_episode = _make_ready_episode(db_session, podcast_dirs, show_b_orm)
    token_a = enabled_a["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token_a}/episodes/{other_episode.id}/audio")

    assert resp.status_code == 404


# --- Public episode chapters route (unauthenticated) --------------------------

def test_public_chapters_returns_the_json_document_for_a_valid_token(auth_client, public_base_url, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = _make_ready_episode(db_session, podcast_dirs, show, shownotes=[
        {"title": "Story A", "source_name": "Source A", "url": "https://a.example/1", "start_seconds": 0.0},
    ])
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/episodes/{episode.id}/chapters.json")

    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.2.0"
    assert body["chapters"] == [{"startTime": 0.0, "title": "Story A (Source A)", "url": "https://a.example/1"}]


def test_public_chapters_404s_without_shownotes(auth_client, public_base_url, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = _make_ready_episode(db_session, podcast_dirs, show)  # no shownotes
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/episodes/{episode.id}/chapters.json")

    assert resp.status_code == 404


def test_public_chapters_404s_for_episode_belonging_to_a_different_show(auth_client, public_base_url, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    show_a = auth_client.post("/api/podcasts/shows", json=_show_payload(name="Show A")).json()
    show_b = auth_client.post("/api/podcasts/shows", json=_show_payload(name="Show B")).json()
    enabled_a = auth_client.post(f"/api/podcasts/shows/{show_a['id']}/public-feed").json()
    show_b_orm = db_session.get(PodcastShow, uuid.UUID(show_b["id"]))
    other_episode = _make_ready_episode(db_session, podcast_dirs, show_b_orm, shownotes=[
        {"title": "Story A", "source_name": "Source A", "url": None, "start_seconds": 0.0},
    ])
    token_a = enabled_a["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token_a}/episodes/{other_episode.id}/chapters.json")

    assert resp.status_code == 404


def test_public_chapters_404s_for_unknown_token(client):
    resp = client.get(f"/api/podcasts/public/not-a-real-token/episodes/{uuid.uuid4()}/chapters.json")
    assert resp.status_code == 404


# --- Public cover route (unauthenticated) -------------------------------------

def test_public_cover_streams_for_valid_token(auth_client, public_base_url, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    buf = BytesIO()
    Image.new("RGB", (20, 20), (255, 0, 0)).save(buf, format="PNG")
    auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", buf.getvalue(), "image/png")},
    )
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/cover")

    assert resp.status_code == 200
    assert Image.open(BytesIO(resp.content)).format == "PNG"


def test_public_cover_404s_when_no_cover_set(auth_client, public_base_url):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/cover")

    assert resp.status_code == 404


def test_public_cover_404s_for_unknown_token(client):
    resp = client.get("/api/podcasts/public/not-a-real-token/cover")
    assert resp.status_code == 404


def test_public_audio_404s_for_non_ready_episode(auth_client, public_base_url, db_session):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    enabled = auth_client.post(f"/api/podcasts/shows/{created['id']}/public-feed").json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="generating")
    db_session.add(episode)
    db_session.commit()
    token = enabled["public_feed_url"].split("/")[-2]

    auth_client.cookies.clear()
    resp = auth_client.get(f"/api/podcasts/public/{token}/episodes/{episode.id}/audio")

    assert resp.status_code == 404
