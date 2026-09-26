"""Capability scopes for API tokens.

An API token is what an MCP client (or any script) authenticates with, and
until now a token could do anything its owner could. These scopes narrow
that per token, so a read-only client and a fully-privileged one can hold
different credentials and revoking one is just deleting that token.

Enforced in services/auth.py::get_current_user, which is the single place
every authenticated request passes through and the only place that knows a
request came from a token rather than a browser session. Doing it there
rather than in the MCP server is the point: the MCP server is a *client*
holding a token, so hiding tools there would be cosmetic -- anyone could
call the REST API directly with the same token. Tool filtering in the MCP
server is a usability layer on top of this, not the boundary.

Cookie-authenticated requests are unrestricted. Scopes limit what a *token*
can do, not what a user can do in their own browser.
"""

SCOPE_READ = "read"
SCOPE_ACT = "act"
SCOPE_CURATE = "curate"
SCOPE_LEARNING = "learning"
SCOPE_PODCASTS = "podcasts"
SCOPE_STATS = "stats"

# Ordered for display; the descriptions are shown in the settings UI.
ALL_SCOPES: dict[str, str] = {
    SCOPE_READ: "Read the feed, articles, sources and categories",
    SCOPE_ACT: "Mark read, like, dislike and bookmark articles",
    SCOPE_CURATE: "Add, edit and delete sources and categories",
    SCOPE_LEARNING: "View and adjust learned interest weights",
    SCOPE_PODCASTS: "List shows and episodes, and generate episodes",
    SCOPE_STATS: "Read statistics and keyword trends",
}

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# path prefix -> (scope for safe methods, scope for writes).
# Longest prefix wins, so more specific entries can override.
_PREFIX_SCOPES: list[tuple[str, str, str]] = [
    ("/api/news", SCOPE_READ, SCOPE_ACT),
    ("/api/clusters", SCOPE_READ, SCOPE_ACT),
    ("/api/sources", SCOPE_READ, SCOPE_CURATE),
    ("/api/categories", SCOPE_READ, SCOPE_CURATE),
    ("/api/tabs", SCOPE_READ, SCOPE_CURATE),
    ("/api/settings", SCOPE_READ, SCOPE_CURATE),
    ("/api/push", SCOPE_READ, SCOPE_CURATE),
    ("/api/learning", SCOPE_LEARNING, SCOPE_LEARNING),
    ("/api/podcasts", SCOPE_PODCASTS, SCOPE_PODCASTS),
    ("/api/stats", SCOPE_STATS, SCOPE_STATS),
]

# Never reachable with a token, at any scope: a token that can mint or
# delete tokens can escalate its own privileges and outlive its revocation.
_TOKEN_FORBIDDEN_PREFIXES = ("/api/tokens", "/api/auth")

# Reachable by any token regardless of its scopes. Self-introspection has to
# be ungated or a restricted client has no way to learn what it may do --
# and /api/tokens, where scopes are otherwise managed, is barred outright.
_UNGATED_PATHS = frozenset({"/api/settings/token-scopes"})


class ScopeDenied(Exception):
    """Raised with the scope that would have been needed, or None when the
    path is barred from token auth entirely."""

    def __init__(self, scope: str | None):
        self.scope = scope
        super().__init__(scope or "forbidden")


def normalize_scopes(scopes: list[str] | None) -> list[str] | None:
    """Drop unknown and duplicate scopes, preserving ALL_SCOPES order.

    None passes through unchanged and means "unrestricted" -- that's what
    every token created before scopes existed carries, so they keep working.
    An explicitly empty list is a real (if useless) choice and stays empty.
    """
    if scopes is None:
        return None
    given = {s.strip().lower() for s in scopes if isinstance(s, str) and s.strip()}
    return [s for s in ALL_SCOPES if s in given]


def required_scope(method: str, path: str) -> str | None:
    """The scope a request needs, or None when no scope gates it."""
    for prefix in _TOKEN_FORBIDDEN_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            raise ScopeDenied(None)

    if path in _UNGATED_PATHS:
        return None

    best: tuple[int, str] | None = None
    for prefix, safe_scope, write_scope in _PREFIX_SCOPES:
        if path == prefix or path.startswith(prefix + "/"):
            scope = safe_scope if method.upper() in _SAFE_METHODS else write_scope
            if best is None or len(prefix) > best[0]:
                best = (len(prefix), scope)
    return best[1] if best else None


def check_request(scopes: list[str] | None, method: str, path: str) -> None:
    """Raise ScopeDenied if a token with `scopes` may not make this request.

    `scopes` of None is unrestricted (pre-scopes tokens), but the forbidden
    prefixes above still apply to it -- those are about what token auth can
    ever reach, not about what a particular token was granted.
    """
    needed = required_scope(method, path)
    if needed is None or scopes is None:
        return
    if needed not in scopes:
        raise ScopeDenied(needed)
