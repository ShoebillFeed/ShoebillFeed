from unittest.mock import patch


def test_health_check_reports_db_ok(client):
    resp = client.get("/api/settings/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["db"] is True


def test_health_check_does_not_require_auth(client):
    # The Docker healthcheck hits this with no session cookie at all.
    resp = client.get("/api/settings/health")
    assert resp.status_code == 200


def test_db_still_usable_after_health_check_closes_its_connection(client, make_user):
    # health_check() now closes its DB connection early (see api/settings.py) --
    # make sure that doesn't leave the request-scoped session unusable for
    # whatever request comes next.
    resp = client.get("/api/settings/health")
    assert resp.status_code == 200

    make_user()
    resp2 = client.get("/api/categories")
    assert resp2.status_code == 401  # no auth cookie set -- but the DB layer itself must respond, not 500


# --- /settings/podcast-health --------------------------------------------

def test_podcast_health_reports_piper_by_default(client, podcast_dirs):
    resp = client.get("/api/settings/podcast-health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "piper"
    assert body["healthy"] is True  # podcast_dirs points it at a writable tmp dir
    assert body["base_url"] is None
    assert body["supports_speech_rate"] is True
    assert body["supports_exaggeration"] is False


def test_podcast_health_does_not_require_auth(client, podcast_dirs):
    resp = client.get("/api/settings/podcast-health")
    assert resp.status_code == 200


def test_podcast_health_reports_network_provider_and_base_url(client, podcast_dirs, monkeypatch):
    from app.config import get_settings
    from app.services.tts.factory import get_tts_provider
    from app.services.tts.network_provider import NetworkTTSProvider

    settings = get_settings()
    monkeypatch.setattr(settings, "tts_provider", "network")
    monkeypatch.setattr(settings, "tts_service_url", "http://tts.internal:8100")
    get_tts_provider.cache_clear()

    try:
        with patch.object(NetworkTTSProvider, "health_check", return_value=True):
            resp = client.get("/api/settings/podcast-health")
        body = resp.json()
        assert body["provider"] == "network"
        assert body["healthy"] is True
        assert body["base_url"] == "http://tts.internal:8100"
    finally:
        get_tts_provider.cache_clear()


def test_podcast_health_reports_supports_speech_rate_from_a_network_provider(client, podcast_dirs, monkeypatch):
    from app.config import get_settings
    from app.services.tts.factory import get_tts_provider
    from app.services.tts.network_provider import NetworkTTSProvider

    settings = get_settings()
    monkeypatch.setattr(settings, "tts_provider", "network")
    monkeypatch.setattr(settings, "tts_service_url", "http://tts.internal:8100")
    get_tts_provider.cache_clear()

    def fake_health_check(self):
        self.supports_speech_rate = False
        return True

    try:
        with patch.object(NetworkTTSProvider, "health_check", fake_health_check):
            resp = client.get("/api/settings/podcast-health")
        assert resp.json()["supports_speech_rate"] is False
    finally:
        get_tts_provider.cache_clear()


def test_podcast_health_reports_supports_exaggeration_from_a_network_provider(client, podcast_dirs, monkeypatch):
    from app.config import get_settings
    from app.services.tts.factory import get_tts_provider
    from app.services.tts.network_provider import NetworkTTSProvider

    settings = get_settings()
    monkeypatch.setattr(settings, "tts_provider", "network")
    monkeypatch.setattr(settings, "tts_service_url", "http://tts.internal:8100")
    get_tts_provider.cache_clear()

    def fake_health_check(self):
        self.supports_exaggeration = True
        return True

    try:
        with patch.object(NetworkTTSProvider, "health_check", fake_health_check):
            resp = client.get("/api/settings/podcast-health")
        assert resp.json()["supports_exaggeration"] is True
    finally:
        get_tts_provider.cache_clear()


def test_podcast_health_reflects_an_unreachable_network_provider(client, podcast_dirs, monkeypatch):
    from app.config import get_settings
    from app.services.tts.factory import get_tts_provider
    from app.services.tts.network_provider import NetworkTTSProvider

    settings = get_settings()
    monkeypatch.setattr(settings, "tts_provider", "network")
    monkeypatch.setattr(settings, "tts_service_url", "http://tts.internal:8100")
    get_tts_provider.cache_clear()

    try:
        with patch.object(NetworkTTSProvider, "health_check", return_value=False):
            resp = client.get("/api/settings/podcast-health")
        assert resp.json()["healthy"] is False
    finally:
        get_tts_provider.cache_clear()


def test_podcast_health_does_not_500_when_get_tts_provider_raises(client, monkeypatch):
    # e.g. TTS_PROVIDER=network with no TTS_SERVICE_URL configured -- the
    # factory raises ValueError constructing the provider at all.
    from app.config import get_settings
    from app.services.tts.factory import get_tts_provider

    settings = get_settings()
    monkeypatch.setattr(settings, "tts_provider", "network")
    monkeypatch.setattr(settings, "tts_service_url", "")
    get_tts_provider.cache_clear()

    try:
        resp = client.get("/api/settings/podcast-health")
        assert resp.status_code == 200
        assert resp.json()["healthy"] is False
    finally:
        get_tts_provider.cache_clear()
