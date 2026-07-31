import os
import uuid
from unittest.mock import MagicMock, patch

from app.models.podcast_episode import PodcastEpisode

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
    assert body["hosts"] == [VALID_HOST]

    listed = auth_client.get("/api/podcasts/shows")
    assert listed.status_code == 200
    assert "Morning Briefing" in [s["name"] for s in listed.json()]


def test_create_show_requires_authentication(client):
    resp = client.post("/api/podcasts/shows", json=_show_payload())
    assert resp.status_code == 401


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
