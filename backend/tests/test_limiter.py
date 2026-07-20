from starlette.requests import Request

from app.limiter import get_client_ip


def _request(headers: dict[str, str], client_host: str = "172.18.0.5") -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": (client_host, 12345),
    }
    return Request(scope)


def test_uses_x_real_ip_when_present():
    # This is the case that matters in production: nginx always connects
    # from the same internal Docker IP, so without this the rate limiter
    # would treat every visitor as one client.
    request = _request({"x-real-ip": "203.0.113.7"})
    assert get_client_ip(request) == "203.0.113.7"


def test_falls_back_to_socket_peer_without_the_header():
    # Local dev without nginx in front of it.
    request = _request({})
    assert get_client_ip(request) == "172.18.0.5"


def test_distinguishes_two_different_real_clients():
    a = _request({"x-real-ip": "203.0.113.7"})
    b = _request({"x-real-ip": "203.0.113.8"})
    assert get_client_ip(a) != get_client_ip(b)
