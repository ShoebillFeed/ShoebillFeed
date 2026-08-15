from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.podcast_episode import PodcastEpisode
from app.models.podcast_show import PodcastShow
from app.services.podcast_scheduling import due_shows

TZ = "Europe/Berlin"


def _frozen_now_utc() -> datetime:
    # Truncated to the minute so schedule_time ("HH:MM", no seconds) comparisons
    # are exact and don't flake near a minute boundary.
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


def _make_show(db_session, user_id, **overrides):
    defaults = dict(
        user_id=user_id,
        name="Morning Briefing",
        hosts=[{"id": "h1", "name": "Alex", "character_prompt": "curious", "voice": "v1"}],
        category_ids=[],
        source_ids=[],
        schedule_time="07:00",
        timezone=TZ,
        is_active=True,
    )
    defaults.update(overrides)
    show = PodcastShow(**defaults)
    db_session.add(show)
    db_session.flush()
    return show


def _local_hhmm(now_utc: datetime, offset: timedelta = timedelta(), tz_name: str = TZ) -> str:
    return (now_utc.astimezone(ZoneInfo(tz_name)) + offset).strftime("%H:%M")


def test_show_scheduled_for_right_now_is_due(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    show = _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc))
    db_session.commit()

    assert [s.id for s in due_shows(db_session, now_utc)] == [show.id]


def test_show_scheduled_for_a_different_time_is_not_due(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc, timedelta(hours=6)))
    db_session.commit()

    assert due_shows(db_session, now_utc) == []


def test_inactive_show_is_never_due_even_if_scheduled_now(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc), is_active=False)
    db_session.commit()

    assert due_shows(db_session, now_utc) == []


def test_show_with_episode_already_created_today_is_not_dispatched_again(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    show = _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc))
    db_session.add(PodcastEpisode(show_id=show.id, user_id=user.id, status="ready"))
    db_session.commit()

    assert due_shows(db_session, now_utc) == []


def test_episode_from_a_previous_day_does_not_block_todays_dispatch(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    show = _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc))
    old_episode = PodcastEpisode(show_id=show.id, user_id=user.id, status="ready")
    db_session.add(old_episode)
    db_session.flush()
    old_episode.created_at = now_utc - timedelta(days=1)
    db_session.commit()

    assert [s.id for s in due_shows(db_session, now_utc)] == [show.id]


def test_invalid_timezone_is_skipped_without_raising(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    _make_show(db_session, user.id, schedule_time="07:00", timezone="Not/AZone")
    db_session.commit()

    assert due_shows(db_session, now_utc) == []


def test_invalid_schedule_time_format_is_skipped_without_raising(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    # Must still fit the column's String(5) limit -- "abcde" is malformed
    # but not too long, unlike e.g. "not-a-time".
    _make_show(db_session, user.id, schedule_time="abcde")
    db_session.commit()

    assert due_shows(db_session, now_utc) == []


def test_dispatch_window_end_is_exclusive(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    # Scheduled exactly 15 minutes ago -- right at the window's exclusive end.
    _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc, timedelta(minutes=-15)))
    db_session.commit()

    assert due_shows(db_session, now_utc) == []


def test_dispatch_window_start_is_inclusive(db_session, make_user):
    user = make_user()
    now_utc = _frozen_now_utc()
    # Scheduled 14 minutes ago -- just inside the window.
    show = _make_show(db_session, user.id, schedule_time=_local_hhmm(now_utc, timedelta(minutes=-14)))
    db_session.commit()

    assert [s.id for s in due_shows(db_session, now_utc)] == [show.id]


def test_only_the_matching_users_show_is_returned(db_session, make_user):
    user1 = make_user(username="u1")
    user2 = make_user(username="u2")
    now_utc = _frozen_now_utc()
    show1 = _make_show(db_session, user1.id, schedule_time=_local_hhmm(now_utc))
    _make_show(db_session, user2.id, schedule_time=_local_hhmm(now_utc, timedelta(hours=6)))
    db_session.commit()

    assert [s.id for s in due_shows(db_session, now_utc)] == [show1.id]
