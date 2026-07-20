from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Behind the frontend's nginx (which always sets X-Real-IP), the raw
    socket peer is nginx itself -- the same for every request from every
    user -- so the default key_func would turn this into a site-wide rate
    limit instead of a per-client one. Trust X-Real-IP when present; fall
    back to the direct peer for local dev without the proxy in front."""
    real_ip = request.headers.get("x-real-ip")
    return real_ip if real_ip else get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)
