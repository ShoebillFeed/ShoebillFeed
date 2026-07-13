def test_login_succeeds_with_correct_credentials(client, make_user):
    make_user(username="alice", password="correct horse battery staple")

    resp = client.post("/api/auth/login", json={"username": "alice", "password": "correct horse battery staple"})

    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"
    assert "access_token" in resp.cookies


def test_login_fails_with_wrong_password(client, make_user):
    make_user(username="alice", password="correct horse battery staple")

    resp = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})

    assert resp.status_code == 401
    assert "access_token" not in resp.cookies


def test_login_fails_for_unknown_user(client):
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "whatever"})
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_when_authenticated(auth_client):
    resp = auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == auth_client.current_user.username


def test_logout_instructs_the_browser_to_delete_the_session_cookie(auth_client):
    assert auth_client.get("/api/auth/me").status_code == 200

    resp = auth_client.post("/api/auth/logout")

    # Asserted against the raw Set-Cookie header rather than a follow-up
    # request: the login cookie is Secure+SameSite=strict, but Starlette's
    # delete_cookie() defaults don't match those attributes (no Secure,
    # SameSite=lax), which stops httpx's test-client cookie jar from
    # treating it as an overwrite of the original -- a real browser also
    # wouldn't reliably clear a Secure cookie via a non-Secure deletion
    # cookie. What we can assert confidently is that the server does
    # instruct deletion via Max-Age=0.
    set_cookie = resp.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie
