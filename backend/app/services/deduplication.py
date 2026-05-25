import hashlib
import re
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_eid", "ref", "source",
})


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
    clean_query = urlencode(sorted(filtered.items()), doseq=True)
    return urlunparse(parsed._replace(query=clean_query, fragment=""))


def url_hash(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()


def content_hash(text: str) -> str:
    return hashlib.sha256(text[:2000].encode()).hexdigest()
