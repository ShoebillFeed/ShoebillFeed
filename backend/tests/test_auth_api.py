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


def test_logout_clears_the_session(client, make_user):
    # Deliberately goes through a real /login call rather than the
    # auth_client fixture's shortcut (which sets the cookie directly via
    # client.cookies.set(), bypassing an actual Set-Cookie response) --
    # the Secure attribute only round-trips correctly through httpx's
    # cookie jar when the cookie was actually received from the server,
    # same as it would be in a real browser.
    make_user(username="alice", password="correct horse battery staple")
    client.post("/api/auth/login", json={"username": "alice", "password": "correct horse battery staple"})

    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_deletion_cookie_matches_the_login_cookies_attributes(auth_client):
    # delete_cookie() must be called with the same httponly/samesite/secure
    # attributes set_cookie() used at login -- a deletion cookie with
    # different attributes isn't guaranteed to be treated as clearing the
    # same cookie by a real browser (this regressed once already).
    resp = auth_client.post("/api/auth/logout")
    set_cookie = resp.headers.get("set-cookie", "")
    assert "Max-Age=0" in set_cookie
    assert "Secure" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=strict" in set_cookie
