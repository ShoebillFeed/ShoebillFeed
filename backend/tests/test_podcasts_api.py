import os
import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from app.models.podcast_episode import PodcastEpisode

VALID_HOST = {"id": "h1", "name": "Alex", "character_prompt": "Curious and upbeat", "voice": "en_US-libritts_r-medium#0"}


def _image_bytes(size=(20, 20), color=(255, 0, 0), fmt="PNG"):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


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


def _make_ready_episode(db_session, podcast_dirs, show, content=b"fake mp3 bytes"):
    episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="ready", duration_seconds=5)
    db_session.add(episode)
    db_session.flush()
    rel_path = f"{show.user_id}/{episode.id}.mp3"
    abs_path = os.path.join(podcast_dirs.podcast_audio_dir, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)
    episode.audio_path = rel_path
    db_session.commit()
    return episode, abs_path


# --- Shows CRUD -------------------------------------------------------------

def test_create_and_list_show(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Morning Briefing"
    assert body["hosts"] == [{**VALID_HOST, "exaggeration": None, "tts_provider": None}]

    listed = auth_client.get("/api/podcasts/shows")
    assert listed.status_code == 200
    assert "Morning Briefing" in [s["name"] for s in listed.json()]


def test_create_show_requires_authentication(client):
    resp = client.post("/api/podcasts/shows", json=_show_payload())
    assert resp.status_code == 401


def test_create_show_persists_a_per_host_exaggeration_value(auth_client):
    host = {**VALID_HOST, "exaggeration": 0.8}
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=[host]))
    assert resp.status_code == 201
    assert resp.json()["hosts"][0]["exaggeration"] == 0.8


def test_create_show_rejects_an_out_of_range_exaggeration(auth_client):
    host = {**VALID_HOST, "exaggeration": 5.0}
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=[host]))
    assert resp.status_code == 422


def test_create_show_persists_a_per_host_tts_provider_pin(auth_client):
    host = {**VALID_HOST, "tts_provider": "network"}
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=[host]))
    assert resp.status_code == 201
    assert resp.json()["hosts"][0]["tts_provider"] == "network"


def test_create_show_rejects_an_unknown_tts_provider(auth_client):
    host = {**VALID_HOST, "tts_provider": "bogus"}
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=[host]))
    assert resp.status_code == 422


def test_create_show_rejects_more_than_three_hosts(auth_client):
    hosts = [{**VALID_HOST, "id": f"h{i}"} for i in range(4)]
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=hosts))
    assert resp.status_code == 422


def test_create_show_rejects_zero_hosts(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=[]))
    assert resp.status_code == 422


def test_create_show_rejects_host_missing_required_field(auth_client):
    incomplete_host = {"id": "h1", "name": "Alex", "voice": "v1"}  # no character_prompt
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(hosts=[incomplete_host]))
    assert resp.status_code == 422


def test_create_show_rejects_length_over_fifteen_minutes(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(target_length_minutes=16))
    assert resp.status_code == 422


def test_create_show_rejects_length_under_one_minute(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(target_length_minutes=0))
    assert resp.status_code == 422


def test_create_show_rejects_malformed_schedule_time(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(schedule_time="7am"))
    assert resp.status_code == 422


def test_create_show_defaults_description_and_speech_rate(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload())
    body = resp.json()
    assert body["description"] is None
    assert body["speech_rate"] == 1.0
    assert body["cover_image_url"] is None


def test_create_show_accepts_description_and_speech_rate(auth_client):
    resp = auth_client.post(
        "/api/podcasts/shows", json=_show_payload(description="Focus on market impact.", speech_rate=1.25)
    )
    body = resp.json()
    assert body["description"] == "Focus on market impact."
    assert body["speech_rate"] == 1.25


def test_create_show_rejects_speech_rate_out_of_range(auth_client):
    resp = auth_client.post("/api/podcasts/shows", json=_show_payload(speech_rate=2.0))
    assert resp.status_code == 422


def test_update_show_can_change_description_and_speech_rate(auth_client):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    resp = auth_client.patch(
        f"/api/podcasts/shows/{created['id']}",
        json={"description": "New concept", "speech_rate": 0.8},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "New concept"
    assert body["speech_rate"] == 0.8


def test_get_show(auth_client):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    resp = auth_client.get(f"/api/podcasts/shows/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_update_show_partial(auth_client):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    resp = auth_client.patch(f"/api/podcasts/shows/{created['id']}", json={"is_active": False, "target_length_minutes": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_active"] is False
    assert body["target_length_minutes"] == 5
    assert body["name"] == "Morning Briefing"  # untouched fields preserved


# --- Cover image -------------------------------------------------------------

def test_upload_cover_sets_url_and_is_retrievable(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", _image_bytes(), "image/png")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["cover_image_url"] == f"/api/podcasts/shows/{created['id']}/cover"

    get_resp = auth_client.get(body["cover_image_url"])
    assert get_resp.status_code == 200
    stored = Image.open(BytesIO(get_resp.content))
    assert stored.format == "PNG"
    assert stored.size == (20, 20)  # smaller than the resize cap -- left untouched


def test_upload_cover_rejects_invalid_image_bytes(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", b"not actually a png", "image/png")},
    )

    assert resp.status_code == 400


def test_upload_cover_downscales_images_larger_than_the_cap(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", _image_bytes(size=(2000, 1000)), "image/png")},
    )
    body = resp.json()

    stored = Image.open(BytesIO(auth_client.get(body["cover_image_url"]).content))
    assert max(stored.size) == 1400
    assert stored.size == (1400, 700)  # aspect ratio preserved


def test_upload_cover_rejects_unsupported_content_type(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()

    resp = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.gif", b"gif bytes", "image/gif")},
    )

    assert resp.status_code == 400


def test_upload_cover_rejects_oversized_file(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    oversized = b"x" * (5 * 1024 * 1024 + 1)

    resp = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", oversized, "image/png")},
    )

    assert resp.status_code == 400


def test_upload_cover_replaces_previous_cover_file(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", _image_bytes(color=(255, 0, 0)), "image/png")},
    )

    resp = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.jpg", _image_bytes(color=(0, 255, 0), fmt="JPEG"), "image/jpeg")},
    )
    body = resp.json()

    get_resp = auth_client.get(body["cover_image_url"])
    assert Image.open(BytesIO(get_resp.content)).format == "JPEG"


def test_delete_cover_clears_url_and_removes_file(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    uploaded = auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", _image_bytes(), "image/png")},
    ).json()

    resp = auth_client.delete(f"/api/podcasts/shows/{created['id']}/cover")

    assert resp.status_code == 200
    assert resp.json()["cover_image_url"] is None
    assert auth_client.get(uploaded["cover_image_url"]).status_code == 404


def test_get_cover_404s_when_none_set(auth_client, podcast_dirs):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    resp = auth_client.get(f"/api/podcasts/shows/{created['id']}/cover")
    assert resp.status_code == 404


def test_delete_show_removes_cover_image_file(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", _image_bytes(), "image/png")},
    )
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    cover_path = os.path.join(podcast_dirs.podcast_audio_dir, show.cover_image_path)
    assert os.path.exists(cover_path)

    auth_client.delete(f"/api/podcasts/shows/{created['id']}")

    assert not os.path.exists(cover_path)


def test_user_cannot_access_another_users_show_cover(client, make_user, podcast_dirs):
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")
    client.cookies.set("access_token", create_token(user1.id, user1.username))
    created = client.post("/api/podcasts/shows", json=_show_payload()).json()

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    resp = client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", b"bytes", "image/png")},
    )
    assert resp.status_code == 404


def test_delete_show(auth_client):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    resp = auth_client.delete(f"/api/podcasts/shows/{created['id']}")
    assert resp.status_code == 204
    assert auth_client.get(f"/api/podcasts/shows/{created['id']}").status_code == 404


def test_delete_show_removes_episode_audio_files(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    _episode, abs_path = _make_ready_episode(db_session, podcast_dirs, show)
    assert os.path.exists(abs_path)

    resp = auth_client.delete(f"/api/podcasts/shows/{created['id']}")
    assert resp.status_code == 204
    assert not os.path.exists(abs_path)


def test_users_only_see_their_own_shows(client, make_user):
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")

    client.cookies.set("access_token", create_token(user1.id, user1.username))
    client.post("/api/podcasts/shows", json=_show_payload(name="User1 Show"))

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    listed = client.get("/api/podcasts/shows").json()
    assert "User1 Show" not in [s["name"] for s in listed]


def test_user_cannot_access_another_users_show_by_id(client, make_user):
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")

    client.cookies.set("access_token", create_token(user1.id, user1.username))
    created = client.post("/api/podcasts/shows", json=_show_payload()).json()

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    assert client.get(f"/api/podcasts/shows/{created['id']}").status_code == 404
    assert client.patch(f"/api/podcasts/shows/{created['id']}", json={"is_active": False}).status_code == 404
    assert client.delete(f"/api/podcasts/shows/{created['id']}").status_code == 404


# --- Generate now -------------------------------------------------------------

def test_generate_now_dispatches_task_on_the_podcast_queue(auth_client):
    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    fake_result = MagicMock(id="fake-task-id")

    with patch("app.tasks.podcast_tasks.generate_podcast_episode.apply_async", return_value=fake_result) as apply_async:
        resp = auth_client.post(f"/api/podcasts/shows/{created['id']}/generate")

    assert resp.status_code == 200
    assert resp.json() == {"queued": True}
    apply_async.assert_called_once()
    assert apply_async.call_args.kwargs["queue"] == "podcast"
    assert apply_async.call_args.kwargs["args"] == [created["id"]]


def test_generate_now_requires_owning_the_show(client, make_user):
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")
    client.cookies.set("access_token", create_token(user1.id, user1.username))
    created = client.post("/api/podcasts/shows", json=_show_payload()).json()

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    with patch("app.tasks.podcast_tasks.generate_podcast_episode.apply_async") as apply_async:
        resp = client.post(f"/api/podcasts/shows/{created['id']}/generate")

    assert resp.status_code == 404
    apply_async.assert_not_called()


# --- Voices -------------------------------------------------------------

def test_list_voices_for_known_language_returns_entries(auth_client, podcast_dirs):
    resp = auth_client.get("/api/podcasts/voices", params={"language": "en"})
    assert resp.status_code == 200
    voices = resp.json()
    assert len(voices) > 0
    assert all("id" in v and "label" in v for v in voices)


def test_list_voices_for_unknown_language_returns_empty_list(auth_client, podcast_dirs):
    resp = auth_client.get("/api/podcasts/voices", params={"language": "xx"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_voices_accepts_an_explicit_provider_override(auth_client, podcast_dirs):
    fake_provider = MagicMock()
    from app.services.tts.base import VoiceInfo
    fake_provider.list_voices.return_value = [VoiceInfo(id="v1", language="en", label="Voice 1")]

    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider) as get_provider:
        resp = auth_client.get("/api/podcasts/voices", params={"language": "en", "provider": "network"})

    assert resp.status_code == 200
    assert resp.json() == [{"id": "v1", "label": "Voice 1"}]
    get_provider.assert_called_once_with("network")


def test_list_voices_returns_400_for_a_misconfigured_provider_override(auth_client, podcast_dirs):
    resp = auth_client.get("/api/podcasts/voices", params={"language": "en", "provider": "network"})
    assert resp.status_code == 400


# --- Voice preview --------------------------------------------------------

def _fake_provider_writing(content: bytes):
    fake_provider = MagicMock()

    def fake_synthesize(text, voice_id, out_path, speech_rate=1.0):
        with open(out_path, "wb") as f:
            f.write(content)

    fake_provider.synthesize.side_effect = fake_synthesize
    return fake_provider


def test_preview_voice_accepts_an_explicit_provider_override(auth_client, podcast_dirs):
    fake_provider = _fake_provider_writing(b"bytes")
    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider) as get_provider:
        resp = auth_client.get(
            "/api/podcasts/voices/preview", params={"voice_id": "v", "language": "en", "provider": "network"}
        )
    assert resp.status_code == 200
    get_provider.assert_called_once_with("network")


def test_preview_voice_returns_400_for_a_misconfigured_provider_override(auth_client, podcast_dirs):
    resp = auth_client.get(
        "/api/podcasts/voices/preview", params={"voice_id": "v", "language": "en", "provider": "network"}
    )
    assert resp.status_code == 400


def test_preview_voice_returns_the_synthesized_audio_bytes(auth_client, podcast_dirs):
    fake_provider = _fake_provider_writing(b"RIFF....fake wav bytes")
    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider):
        resp = auth_client.get(
            "/api/podcasts/voices/preview", params={"voice_id": "en_US-libritts_r-medium#0", "language": "en"}
        )

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert resp.content == b"RIFF....fake wav bytes"


def test_preview_voice_uses_a_language_appropriate_sample_phrase(auth_client, podcast_dirs):
    fake_provider = _fake_provider_writing(b"bytes")
    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider):
        auth_client.get("/api/podcasts/voices/preview", params={"voice_id": "de_DE-mls-medium", "language": "de"})

    call_args = fake_provider.synthesize.call_args
    assert call_args.args[0] == "Hallo, das ist eine Vorschau dieser Stimme."
    assert call_args.args[1] == "de_DE-mls-medium"


def test_preview_voice_falls_back_to_english_for_an_uncatalogued_language(auth_client, podcast_dirs):
    fake_provider = _fake_provider_writing(b"bytes")
    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider):
        auth_client.get("/api/podcasts/voices/preview", params={"voice_id": "v", "language": "xx"})

    assert fake_provider.synthesize.call_args.args[0] == "Hello, this is a preview of this voice."


def test_preview_voice_returns_400_for_an_unknown_voice(auth_client, podcast_dirs):
    fake_provider = MagicMock()
    fake_provider.synthesize.side_effect = ValueError("Unknown Piper voice model: 'bogus'")
    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider):
        resp = auth_client.get("/api/podcasts/voices/preview", params={"voice_id": "bogus", "language": "en"})
    assert resp.status_code == 400


def test_preview_voice_requires_auth(client, podcast_dirs):
    resp = client.get("/api/podcasts/voices/preview", params={"voice_id": "v", "language": "en"})
    assert resp.status_code == 401


def test_preview_voice_removes_the_temp_file_afterward(auth_client, podcast_dirs):
    captured_path = {}
    fake_provider = MagicMock()

    def fake_synthesize(text, voice_id, out_path, speech_rate=1.0):
        captured_path["path"] = out_path
        with open(out_path, "wb") as f:
            f.write(b"bytes")

    fake_provider.synthesize.side_effect = fake_synthesize
    with patch("app.services.tts.factory.get_tts_provider", return_value=fake_provider):
        auth_client.get("/api/podcasts/voices/preview", params={"voice_id": "v", "language": "en"})

    assert not os.path.exists(captured_path["path"])


# --- Episodes -------------------------------------------------------------

def test_list_show_episodes(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode, _ = _make_ready_episode(db_session, podcast_dirs, show)

    resp = auth_client.get(f"/api/podcasts/shows/{created['id']}/episodes")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == str(episode.id)
    assert body[0]["show_name"] == "Morning Briefing"
    assert body[0]["show_cover_image_url"] is None


def test_list_show_episodes_includes_show_cover_image_url_when_set(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    auth_client.post(
        f"/api/podcasts/shows/{created['id']}/cover",
        files={"file": ("cover.png", _image_bytes(), "image/png")},
    )
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    _make_ready_episode(db_session, podcast_dirs, show)

    resp = auth_client.get(f"/api/podcasts/shows/{created['id']}/episodes")

    assert resp.json()[0]["show_cover_image_url"] == f"/api/podcasts/shows/{created['id']}/cover"


def test_episode_description_reflects_shownotes_when_present(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode, _ = _make_ready_episode(db_session, podcast_dirs, show)
    episode.shownotes = [
        {"title": "Big Story", "source_name": "The Daily", "url": "https://example.com/1", "start_seconds": 5.0},
    ]
    db_session.commit()

    resp = auth_client.get(f"/api/podcasts/episodes/{episode.id}")

    assert "Big Story" in resp.json()["description"]
    assert "The Daily" in resp.json()["description"]


def test_list_all_episodes_is_paginated_and_includes_show_name(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    for _ in range(3):
        _make_ready_episode(db_session, podcast_dirs, show)

    resp = auth_client.get("/api/podcasts/episodes", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["pages"] == 2
    assert len(body["items"]) == 2
    assert all(item["show_name"] == "Morning Briefing" for item in body["items"])


def test_get_episode_detail(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode, _ = _make_ready_episode(db_session, podcast_dirs, show)

    resp = auth_client.get(f"/api/podcasts/episodes/{episode.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_episode_not_found_for_another_user(client, make_user, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")
    client.cookies.set("access_token", create_token(user1.id, user1.username))
    created = client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode, _ = _make_ready_episode(db_session, podcast_dirs, show)

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    assert client.get(f"/api/podcasts/episodes/{episode.id}").status_code == 404


def test_delete_episode_removes_audio_file(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode, abs_path = _make_ready_episode(db_session, podcast_dirs, show)

    resp = auth_client.delete(f"/api/podcasts/episodes/{episode.id}")
    assert resp.status_code == 204
    assert not os.path.exists(abs_path)
    assert auth_client.get(f"/api/podcasts/episodes/{episode.id}").status_code == 404


# --- Regenerate episode -----------------------------------------------------

def test_regenerate_dispatches_task_on_the_podcast_queue(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="failed", error_message="boom")
    db_session.add(episode)
    db_session.commit()

    fake_result = MagicMock(id="fake-task-id")
    with patch(
        "app.tasks.podcast_tasks.regenerate_podcast_episode.apply_async", return_value=fake_result
    ) as apply_async:
        resp = auth_client.post(f"/api/podcasts/episodes/{episode.id}/regenerate")

    assert resp.status_code == 200
    assert resp.json() == {"queued": True}
    apply_async.assert_called_once()
    assert apply_async.call_args.kwargs["queue"] == "podcast"
    assert apply_async.call_args.kwargs["args"] == [str(episode.id)]


def test_regenerate_rejects_an_episode_already_generating(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="generating")
    db_session.add(episode)
    db_session.commit()

    with patch("app.tasks.podcast_tasks.regenerate_podcast_episode.apply_async") as apply_async:
        resp = auth_client.post(f"/api/podcasts/episodes/{episode.id}/regenerate")

    assert resp.status_code == 409
    apply_async.assert_not_called()


def test_regenerate_requires_owning_the_episode(client, db_session, make_user, podcast_dirs):
    from app.models.podcast_show import PodcastShow
    from app.services.auth import create_token

    user1 = make_user(username="user1")
    user2 = make_user(username="user2")
    client.cookies.set("access_token", create_token(user1.id, user1.username))
    created = client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="ready")
    db_session.add(episode)
    db_session.commit()

    client.cookies.set("access_token", create_token(user2.id, user2.username))
    with patch("app.tasks.podcast_tasks.regenerate_podcast_episode.apply_async") as apply_async:
        resp = client.post(f"/api/podcasts/episodes/{episode.id}/regenerate")

    assert resp.status_code == 404
    apply_async.assert_not_called()


def test_regenerate_404_for_an_unknown_episode(auth_client, podcast_dirs):
    with patch("app.tasks.podcast_tasks.regenerate_podcast_episode.apply_async") as apply_async:
        resp = auth_client.post(f"/api/podcasts/episodes/{uuid.uuid4()}/regenerate")

    assert resp.status_code == 404
    apply_async.assert_not_called()


# --- Audio streaming -------------------------------------------------------------

def test_stream_audio_404_when_episode_not_ready(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    episode = PodcastEpisode(show_id=show.id, user_id=show.user_id, status="generating")
    db_session.add(episode)
    db_session.commit()

    resp = auth_client.get(f"/api/podcasts/episodes/{episode.id}/audio")
    assert resp.status_code == 404


def test_stream_audio_full_file_without_range_header(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    content = b"0123456789" * 100
    episode, _ = _make_ready_episode(db_session, podcast_dirs, show, content=content)

    resp = auth_client.get(f"/api/podcasts/episodes/{episode.id}/audio")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert resp.content == content


def test_stream_audio_returns_206_for_range_request(auth_client, db_session, podcast_dirs):
    from app.models.podcast_show import PodcastShow

    created = auth_client.post("/api/podcasts/shows", json=_show_payload()).json()
    show = db_session.get(PodcastShow, uuid.UUID(created["id"]))
    content = b"0123456789" * 100  # 1000 bytes
    episode, _ = _make_ready_episode(db_session, podcast_dirs, show, content=content)

    resp = auth_client.get(f"/api/podcasts/episodes/{episode.id}/audio", headers={"Range": "bytes=10-19"})
    assert resp.status_code == 206
    assert resp.headers["content-range"] == "bytes 10-19/1000"
    assert resp.headers["content-length"] == "10"
    assert resp.headers["accept-ranges"] == "bytes"
    assert resp.content == content[10:20]
