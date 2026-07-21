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
