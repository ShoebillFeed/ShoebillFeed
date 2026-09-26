#!/usr/bin/env python3
"""Shoebill Feed MCP Server.

Exposes your Shoebill Feed instance as an MCP tool server so Claude and other
MCP clients can read, search, and interact with your personal news feed.

Configuration (environment variables):
  SHOEBILL_API_URL    Base URL of the Shoebill API, e.g. http://localhost:8000/api
  SHOEBILL_API_TOKEN  API token generated in Settings → Preferences → API Tokens

Run with:
  uv run --with 'mcp>=2' --with httpx server.py
  # or after: pip install mcp httpx
  python server.py
"""

import json
import os
import sys
from urllib.parse import quote
from typing import Any

try:
    import httpx
    from mcp.server import MCPServer
except ImportError:
    print("Missing dependencies. Install with: pip install mcp httpx", file=sys.stderr)
    sys.exit(1)

API_URL = os.environ.get("SHOEBILL_API_URL", "http://localhost:8000/api").rstrip("/")
API_TOKEN = os.environ.get("SHOEBILL_API_TOKEN", "")

if not API_TOKEN:
    print(
        "SHOEBILL_API_TOKEN is not set. "
        "Generate one in Settings → Preferences → API Tokens.",
        file=sys.stderr,
    )
    sys.exit(1)

_HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


def _get(path: str, params: dict | None = None) -> Any:
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{API_URL}{path}", headers=_HEADERS, params=params)
        resp.raise_for_status()
        return resp.json()


def _post(path: str, body: dict | None = None, params: dict | None = None) -> Any:
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{API_URL}{path}", headers=_HEADERS, json=body or {}, params=params
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {}


def _delete(path: str) -> None:
    with httpx.Client(timeout=30) as client:
        resp = client.delete(f"{API_URL}{path}", headers=_HEADERS)
        resp.raise_for_status()


def _patch(path: str, body: dict | None = None) -> Any:
    with httpx.Client(timeout=30) as client:
        resp = client.patch(
            f"{API_URL}{path}", headers=_HEADERS, json=body or {}
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {}


# The feed mixes two resource types that live under different API prefixes:
# standalone articles at /news/{id} and multi-source stories at
# /clusters/{id}. They were previously rendered identically, so the model
# would read a cluster's bare UUID out of the feed and every action tool
# would aim it at /news/{id} -- a 404, i.e. a like or bookmark that silently
# did nothing on exactly the stories a reader most wants to act on.
# Cluster IDs are therefore exposed with a "cluster:" prefix, which makes
# them self-describing: no extra probe request, and no reliance on the model
# passing a separate kind argument it would have to remember.
_CLUSTER_PREFIX = "cluster:"


def _is_cluster(entry: dict) -> bool:
    return entry.get("kind") == "cluster"


def _exposed_id(entry: dict) -> str:
    """The ID string handed to the model for a feed entry."""
    return (_CLUSTER_PREFIX if _is_cluster(entry) else "") + str(entry["id"])


def _resolve_id(raw: str) -> tuple[str, str]:
    """Split an exposed ID into (api_prefix, plain_id).

    A bare UUID stays an article, so IDs from search results (which are
    always articles -- /news/search returns no clusters) keep working
    untouched.
    """
    raw = (raw or "").strip()
    if raw.startswith(_CLUSTER_PREFIX):
        return "/clusters", raw[len(_CLUSTER_PREFIX):].strip()
    return "/news", raw


def _fmt_item(item: dict) -> str:
    lines = []
    if item.get("title"):
        lines.append(f"**{item['title']}**")
    cats = ", ".join(c["name"] for c in item.get("categories", []))
    if cats:
        lines.append(f"Categories: {cats}")
    # A cluster carries unified_abstract, not abstract -- reading only the
    # latter meant clustered stories previously showed no summary at all.
    abstract = item.get("abstract") or item.get("unified_abstract")
    if abstract:
        lines.append(abstract)
    if item.get("url"):
        lines.append(f"URL: {item['url']}")
    meta = []
    if _is_cluster(item):
        members = item.get("items", [])
        names = [m["source"]["name"] for m in members if m.get("source")]
        # Clusters have no top-level source; the member sources are the
        # point of a cluster, so name them rather than showing nothing.
        meta.append(f"{len(members)} sources" + (f" ({', '.join(names)})" if names else ""))
    elif item.get("source"):
        meta.append(item["source"]["name"])
    if item.get("relevance_score"):
        meta.append(f"Relevance: {item['relevance_score']}/10")
    if item.get("impact_score"):
        meta.append(f"Impact: {item['impact_score']}/10")
    if item.get("published_at"):
        meta.append(item["published_at"][:10])
    if meta:
        lines.append(" · ".join(meta))
    flags = []
    if item.get("is_read"):
        flags.append("read")
    if item.get("is_relevant"):
        flags.append("liked")
    if item.get("read_later"):
        flags.append("bookmarked")
    if flags:
        lines.append(f"[{', '.join(flags)}]")
    lines.append(f"ID: {_exposed_id(item)}")
    if _is_cluster(item):
        for member in item.get("items", []):
            title = member.get("title") or ""
            url = member.get("url") or ""
            lines.append(f"  - {title} ({url})")
    return "\n".join(lines)

def _handle(name: str, args: dict) -> str:
    if name == "get_feed":
        tab = args.get("tab", "newest")
        page_size = min(int(args.get("page_size", 20)), 50)
        params: dict = {"tab": tab if tab != "read_later" else "newest", "page_size": page_size}
        if args.get("unread_only"):
            params["is_read"] = False
        if tab == "read_later":
            params["read_later"] = True
        if args.get("category_ids"):
            params["category_ids"] = args["category_ids"]
        if args.get("source_ids"):
            params["source_ids"] = args["source_ids"]
        data = _get("/news", params)
        items = data.get("items", [])
        if not items:
            return "No items found."
        return "\n\n---\n\n".join(_fmt_item(i) for i in items)

    if name == "search_news":
        query = args["query"]
        page_size = min(int(args.get("page_size", 50)), 50)
        params = {"q": query, "page_size": page_size, "sort": args.get("sort", "newest")}
        if args.get("unread_only"):
            params["is_read"] = False
        if args.get("bookmarked_only"):
            params["read_later"] = True
        if args.get("category_ids"):
            params["category_ids"] = args["category_ids"]
        if args.get("source_ids"):
            params["source_ids"] = args["source_ids"]
        items = _get("/news/search", params)
        if not items:
            return f"No results for '{query}'."
        return f"Results for '{query}':\n\n" + "\n\n---\n\n".join(_fmt_item(i) for i in items)

    if name == "get_item":
        base, ident = _resolve_id(args["id"])
        item = _get(f"{base}/{ident}")
        lines = [_fmt_item(item)]
        if item.get("raw_content"):
            lines.append(f"\nContent:\n{item['raw_content'][:3000]}")
        return "\n".join(lines)

    if name == "mark_read":
        base, ident = _resolve_id(args["id"])
        item = _get(f"{base}/{ident}")
        if not item.get("is_read"):
            _patch(f"{base}/{ident}/read")
        return "Marked as read."

    if name == "mark_unread":
        base, ident = _resolve_id(args["id"])
        item = _get(f"{base}/{ident}")
        if item.get("is_read"):
            _patch(f"{base}/{ident}/read")
        return "Marked as unread."

    if name == "mark_all_read":
        # Already covers clusters server-side (api/news.py::mark_all_read
        # sweeps NewsItem and NewsCluster both), so no routing needed here.
        _post("/news/mark-all-read")
        return "All items marked as read."

    if name == "like":
        # Pre-checked like every other action below: /relevant is a toggle,
        # so an unconditional PATCH turned a second "like" into an un-like.
        base, ident = _resolve_id(args["id"])
        item = _get(f"{base}/{ident}")
        if not item.get("is_relevant"):
            _patch(f"{base}/{ident}/relevant")
        return "Liked."

    if name == "dislike":
        # Not a toggle -- /dislike sets is_read=True, is_relevant=False --
        # so this one is already idempotent and needs no pre-read.
        base, ident = _resolve_id(args["id"])
        _patch(f"{base}/{ident}/dislike")
        return "Disliked."

    if name == "bookmark":
        base, ident = _resolve_id(args["id"])
        item = _get(f"{base}/{ident}")
        if not item.get("read_later"):
            _patch(f"{base}/{ident}/read-later")
        return "Added to Read Later."

    if name == "unbookmark":
        base, ident = _resolve_id(args["id"])
        item = _get(f"{base}/{ident}")
        if item.get("read_later"):
            _patch(f"{base}/{ident}/read-later")
        return "Removed from Read Later."

    if name == "get_digest":
        tab = args.get("tab", "relevant")
        page_size = min(int(args.get("page_size", 10)), 50)
        data = _get("/news", {"tab": tab, "page_size": page_size})
        items = data.get("items", [])
        if not items:
            return "No items in the digest."
        lines = [f"Top {len(items)} items ({tab}):"]
        for i, item in enumerate(items, 1):
            score = item.get("relevance_score") or item.get("impact_score") or ""
            score_str = f" [{score}/10]" if score else ""
            cats = ", ".join(c["name"] for c in item.get("categories", []))
            cats_str = f" ({cats})" if cats else ""
            source = (item.get("source") or {}).get("name", "")
            source_str = f" — {source}" if source else ""
            abstract = item.get("abstract", "")
            lines.append(f"\n{i}. **{item['title']}**{score_str}{cats_str}{source_str}")
            if abstract:
                lines.append(f"   {abstract}")
            lines.append(f"   {item['url']}")
        return "\n".join(lines)

    if name == "list_sources":
        sources = _get("/sources")
        if not sources:
            return "No sources configured."
        lines = []
        for s in sources:
            active = "✓" if s.get("is_active") else "✗"
            lines.append(f"{active} {s['name']} ({s.get('source_type', 'unknown')}) — id:{s['id']}")
        return "\n".join(lines)

    if name == "list_categories":
        cats = _get("/categories")
        if not cats:
            return "No categories."
        lines = []
        for c in cats:
            active = "✓" if c.get("is_active") else "✗"
            lines.append(f"{active} {c['name']} — id:{c['id']}")
        return "\n".join(lines)

    if name == "trigger_fetch":
        _post("/sources/fetch-all")
        return "Fetch triggered. New articles will appear within a minute."

    # ── Learning profile ────────────────────────────────────────────────────

    if name == "get_learning_profile":
        profile = _get("/learning/profile")
        lines = ["**Categories** (learned x manual = effective ranking weight)"]
        for cat in profile.get("categories", []):
            learned, manual = cat["learned_weight"], cat["manual_weight"]
            lines.append(
                f"- {cat['name']}: learned {learned}, manual {manual}, "
                f"effective {round(learned * manual, 3)} "
                f"({cat['total_marked']} marked relevant) [id: {cat['id']}]"
            )
        keywords = profile.get("keywords", [])
        if keywords:
            lines.append("\n**Top learned keywords**")
            for kw in keywords:
                lines.append(f"- {kw['keyword']}: {kw['weight']} ({kw['total_marked']} marked)")
        return "\n".join(lines) if len(lines) > 1 else "Nothing learned yet — like some articles first."

    if name == "set_category_weight":
        weight = float(args["manual_weight"])
        if not 0.0 <= weight <= 5.0:
            return "manual_weight must be between 0.0 and 5.0."
        _patch(f"/learning/categories/{args['category_id']}/weight", {"manual_weight": weight})
        return f"Manual weight set to {weight} (1.0 is neutral)."

    if name == "forget_keyword":
        # 204 whether or not the keyword existed, so this is idempotent and
        # there's nothing to report back beyond the normalized form.
        _delete(f"/learning/keywords/{quote(str(args['keyword']), safe='')}")
        return f"Forgot learned keyword {args['keyword']!r}."

    # ── Source curation ─────────────────────────────────────────────────────

    if name == "add_source":
        body = {
            "name": args["name"],
            "source_type": args["source_type"],
            "config": args.get("config") or {},
        }
        if args.get("fetch_interval"):
            body["fetch_interval"] = int(args["fetch_interval"])
        src = _post("/sources", body)
        return (f"Created source '{src['name']}' ({src['source_type']}), id {src['id']}. "
                f"Call fetch_source to pull it now and confirm it works.")

    if name == "update_source":
        body = {k: args[k] for k in ("name", "config", "is_active", "fetch_interval") if k in args}
        if not body:
            return "Nothing to update — pass at least one of name, config, is_active, fetch_interval."
        src = _patch(f"/sources/{args['id']}", body)
        state = "active" if src.get("is_active") else "paused"
        return f"Updated '{src['name']}' ({state})."

    if name == "delete_source":
        _delete(f"/sources/{args['id']}")
        return "Source deleted."

    if name == "fetch_source":
        _post(f"/sources/{args['id']}/fetch")
        return "Fetch queued for that source. Give it a few seconds, then check get_feed."

    if name == "list_shared_sources":
        shared = _get("/sources/shared")
        if not shared:
            return "No shared sources available."
        return "\n".join(
            f"- {x.get('name')} ({x.get('source_type')}) [id: {x.get('id')}]" for x in shared
        )

    if name == "suggest_scraper_config":
        suggestion = _post("/sources/scraper/suggest", {"url": args["url"]})
        return json.dumps(suggestion, indent=2)

    if name == "export_sources":
        return json.dumps(_get("/sources/export"), indent=2)

    # ── Category curation ───────────────────────────────────────────────────

    if name == "add_category":
        body: dict = {"name": args["name"]}
        for key in ("keywords", "color", "prompt"):
            if key in args:
                body[key] = args[key]
        cat = _post("/categories", body)
        return f"Created category '{cat['name']}', id {cat['id']}."

    if name == "update_category":
        body = {k: args[k] for k in ("name", "keywords", "color", "prompt", "is_active") if k in args}
        if not body:
            return "Nothing to update — pass at least one field."
        cat = _patch(f"/categories/{args['id']}", body)
        return f"Updated category '{cat['name']}'."

    if name == "delete_category":
        _delete(f"/categories/{args['id']}")
        return "Category deleted."

    # ── Podcasts ────────────────────────────────────────────────────────────

    if name == "list_podcast_shows":
        shows = _get("/podcasts/shows")
        if not shows:
            return "No podcast shows configured."
        lines = []
        for show in shows:
            bits = [f"**{show.get('name')}**"]
            if show.get("schedule_time"):
                bits.append(f"daily at {show['schedule_time']} {show.get('timezone', 'UTC')}")
            if show.get("target_length_minutes"):
                bits.append(f"~{show['target_length_minutes']} min")
            if show.get("language"):
                bits.append(show["language"])
            line = " · ".join(bits)
            if show.get("public_feed_enabled") and show.get("public_feed_url"):
                line += f"\n  Public feed: {show['public_feed_url']}"
            line += f"\n  id: {show.get('id')}"
            lines.append(line)
        return "\n\n".join(lines)

    if name == "list_podcast_episodes":
        page_size = min(int(args.get("page_size", 10)), 100)
        data = _get("/podcasts/episodes", {"page_size": page_size})
        episodes = data.get("items", [])
        if not episodes:
            return "No episodes yet."
        lines = []
        for ep in episodes:
            bits = [f"**{ep.get('show_name') or 'Episode'}** — {ep.get('status')}"]
            if ep.get("duration_seconds"):
                bits.append(f"{round(ep['duration_seconds'] / 60)} min")
            if ep.get("generated_at"):
                bits.append(ep["generated_at"][:16].replace("T", " "))
            line = " · ".join(bits)
            if ep.get("error_message"):
                line += f"\n  Error: {ep['error_message']}"
            for note in (ep.get("shownotes") or [])[:8]:
                line += f"\n  - {note.get('title')}"
            line += f"\n  id: {ep.get('id')}"
            lines.append(line)
        return "\n\n".join(lines)

    if name == "generate_podcast_episode":
        _post(f"/podcasts/shows/{args['show_id']}/generate")
        return ("Episode queued. Script generation and speech synthesis take several "
                "minutes; check list_podcast_episodes for status.")

    if name == "get_podcast_feed_url":
        show_id = args["show_id"]
        show = _get(f"/podcasts/shows/{show_id}")
        if not show.get("public_feed_enabled"):
            if not args.get("enable"):
                return ("The public feed is disabled for this show. Re-run with enable=true "
                        "to turn it on — note the resulting URL is unauthenticated, so "
                        "anyone holding it can fetch the audio.")
            show = _post(f"/podcasts/shows/{show_id}/public-feed")
        url = show.get("public_feed_url")
        if not url:
            return ("The feed is enabled but the server has no PUBLIC_BASE_URL configured, "
                    "so it cannot build a usable URL.")
        return f"Public RSS feed: {url}"

    # ── Trends ──────────────────────────────────────────────────────────────

    if name == "keyword_momentum":
        direction = args.get("direction", "rising")
        limit = min(int(args.get("limit", 15)), 50)
        rows = _get("/stats/keyword-momentum", {"direction": direction})
        if not rows:
            return f"No {direction} keywords found — needs a few months of history."
        lines = []
        for row in rows[:limit]:
            bits = [f"**{row.get('keyword')}**"]
            for field, label in (("weekly_slope", "weekly"), ("monthly_slope", "monthly")):
                if row.get(field) is not None:
                    bits.append(f"{label} {row[field]:+.2f}")
            if row.get("total_mentions") is not None:
                bits.append(f"{row['total_mentions']} mentions")
            if row.get("is_newcomer"):
                bits.append("NEW")
            if row.get("is_dormant"):
                bits.append("DORMANT")
            lines.append(" · ".join(bits))
        return f"**{direction.title()} keywords**\n" + "\n".join(lines)

    if name == "keyword_trend":
        topics = args["topics"]
        if not isinstance(topics, list) or not topics:
            return "Pass at least one topic as {label, keywords[]}."
        body = {"topics": [{"label": t["label"], "keywords": t["keywords"]} for t in topics[:6]]}
        # days is intentionally omitted (not sent as null) when absent: the
        # endpoint treats an explicit null as "all time".
        if "days" in args:
            body["days"] = args["days"]
        results = _post("/stats/keyword-trend", body)
        lines = []
        for result in results:
            points = result.get("points", [])
            total = sum(p.get("count", 0) for p in points)
            lines.append(f"**{result.get('label')}** — {total} articles total")
            for point in points:
                if point.get("count"):
                    lines.append(f"  {point.get('date')}: {point['count']}")
        return "\n".join(lines) if lines else "No matches in that window."

    return f"Unknown tool: {name}"


# ── Tool surface ────────────────────────────────────────────────────────────
#
# mcp 2.x derives a tool's input schema from the Python signature and its
# description from the docstring, replacing the hand-written JSON schemas the
# 1.x low-level API needed. Each tool below is a thin typed wrapper over
# _handle(), which keeps every tool's behaviour in one dispatcher and makes
# the signature the single source of truth for the schema -- under 1.x the
# schema and the handler branch were separate and could drift apart.
#
# Optional arguments default to None and are stripped before dispatch,
# because several handlers distinguish "absent" from "explicitly set"
# (update_source's partial patch, keyword_trend's days=None meaning all time).

mcp = MCPServer("shoebill-feed")

# Which scope each tool's underlying API calls need. Kept in lockstep with
# backend/app/services/token_scopes.py -- a tool listed under the wrong scope
# here is only a cosmetic bug, because the API enforces the real boundary and
# would reject the call anyway; the cost is a tool the model can see and
# cannot use.
_TOOL_SCOPES: dict[str, str] = {
    'get_feed': 'read',
    'search_news': 'read',
    'get_item': 'read',
    'get_digest': 'read',
    'mark_read': 'act',
    'mark_unread': 'act',
    'mark_all_read': 'act',
    'like': 'act',
    'dislike': 'act',
    'bookmark': 'act',
    'unbookmark': 'act',
    'get_learning_profile': 'learning',
    'set_category_weight': 'learning',
    'forget_keyword': 'learning',
    'list_sources': 'read',
    'add_source': 'curate',
    'update_source': 'curate',
    'delete_source': 'curate',
    'fetch_source': 'curate',
    'trigger_fetch': 'curate',
    'list_shared_sources': 'read',
    'suggest_scraper_config': 'curate',
    'export_sources': 'curate',
    'list_categories': 'read',
    'add_category': 'curate',
    'update_category': 'curate',
    'delete_category': 'curate',
    'list_podcast_shows': 'podcasts',
    'list_podcast_episodes': 'podcasts',
    'generate_podcast_episode': 'podcasts',
    'get_podcast_feed_url': 'podcasts',
    'keyword_momentum': 'stats',
    'keyword_trend': 'stats',
}


def _granted_scopes() -> list[str] | None:
    """Scopes of the token we hold, or None for unrestricted.

    /api/settings/token-scopes is ungated precisely so this works for a
    restricted token. Any failure (old server without the endpoint, network
    blip) returns None: better to offer every tool and let the API reject
    what isn't permitted than to silently hide the whole surface.
    """
    try:
        return _get("/settings/token-scopes").get("scopes")
    except Exception:
        return None


def _apply_scope_filter() -> None:
    """Remove tools this token cannot use, so the model isn't offered them.

    Purely a usability layer. The security boundary is the API's own scope
    check, which applies whether or not a client bothers to filter -- see
    the module docstring in backend/app/services/token_scopes.py.
    """
    granted = _granted_scopes()
    if granted is None:
        return
    allowed = set(granted)
    for tool_name, needed in _TOOL_SCOPES.items():
        if needed not in allowed:
            mcp.remove_tool(tool_name)



def _call(_tool: str, /, **kwargs: Any) -> str:
    """Dispatch to _handle, dropping unset optional arguments, and turn API
    failures into readable text rather than a protocol-level error.

    The tool name is positional-only: four tools take a parameter literally
    called `name` (add_source, update_source, add_category, update_category),
    which would otherwise collide with this function's own first argument.
    """
    args = {k: v for k, v in kwargs.items() if v is not None}
    try:
        return _handle(_tool, args)
    except httpx.HTTPStatusError as exc:
        return f"API error {exc.response.status_code}: {exc.response.text}"
    except Exception as exc:
        return f"Error: {exc}"


# ── Reading ─────────────────────────────────────────────────────────────────

@mcp.tool()
def get_feed(
    tab: str = "newest",
    page_size: int = 20,
    unread_only: bool = False,
    category_ids: list[str] | None = None,
    source_ids: list[str] | None = None,
) -> str:
    """Read the news feed. `tab` is newest, relevant, impact, or read_later.
    Multi-source stories come back with a cluster:<uuid> ID -- pass that
    whole string back to any action tool."""
    return _call("get_feed", tab=tab, page_size=page_size, unread_only=unread_only,
                 category_ids=category_ids, source_ids=source_ids)


@mcp.tool()
def search_news(query: str, page_size: int = 50, sort: str = "newest") -> str:
    """Full-text search across article titles and abstracts. `sort` is
    newest, relevant, or impact. Returns articles only, never clusters."""
    return _call("search_news", query=query, page_size=page_size, sort=sort)


@mcp.tool()
def get_item(id: str) -> str:
    """Full details for one article or cluster, including its raw content.
    Pass the ID exactly as the feed showed it, cluster: prefix included."""
    return _call("get_item", id=id)


@mcp.tool()
def get_digest(tab: str = "relevant", page_size: int = 10) -> str:
    """A short readable digest of the top items, for summarizing the day."""
    return _call("get_digest", tab=tab, page_size=page_size)


# ── Acting on articles ──────────────────────────────────────────────────────

@mcp.tool()
def mark_read(id: str) -> str:
    """Mark an article or cluster as read. Idempotent."""
    return _call("mark_read", id=id)


@mcp.tool()
def mark_unread(id: str) -> str:
    """Mark an article or cluster as unread. Idempotent."""
    return _call("mark_unread", id=id)


@mcp.tool()
def mark_all_read() -> str:
    """Mark every unread article and cluster as read."""
    return _call("mark_all_read")


@mcp.tool()
def like(id: str) -> str:
    """Mark an article or cluster relevant. This trains ranking: it raises
    the learned weight of its categories and keywords. Idempotent."""
    return _call("like", id=id)


@mcp.tool()
def dislike(id: str) -> str:
    """Mark an article or cluster as not relevant, downgrading similar
    future articles."""
    return _call("dislike", id=id)


@mcp.tool()
def bookmark(id: str) -> str:
    """Add an article or cluster to Read Later. Idempotent. Read Later also
    exempts it from the 30-day cleanup sweep."""
    return _call("bookmark", id=id)


@mcp.tool()
def unbookmark(id: str) -> str:
    """Remove an article or cluster from Read Later. Idempotent."""
    return _call("unbookmark", id=id)


# ── Learning profile ────────────────────────────────────────────────────────

@mcp.tool()
def get_learning_profile() -> str:
    """What Shoebill has learned about the user's interests: per-category
    learned and manual weights with how many articles were marked in each,
    plus top learned keyword weights. Use this to explain WHY something ranks
    highly, or before adjusting a preference."""
    return _call("get_learning_profile")


@mcp.tool()
def set_category_weight(category_id: str, manual_weight: float) -> str:
    """Set a category's manual weight multiplier (0.0-5.0). This is the
    user-controlled dial; it multiplies the separately learned weight rather
    than replacing it. 1.0 is neutral, 0.0 suppresses the category."""
    return _call("set_category_weight", category_id=category_id, manual_weight=manual_weight)


@mcp.tool()
def forget_keyword(keyword: str) -> str:
    """Delete a learned keyword weight so it stops influencing ranking. Use
    when a keyword was learned by accident."""
    return _call("forget_keyword", keyword=keyword)


# ── Sources ─────────────────────────────────────────────────────────────────

@mcp.tool()
def list_sources() -> str:
    """List configured news sources with their type and article counts."""
    return _call("list_sources")


@mcp.tool()
def add_source(
    name: str,
    source_type: str,
    config: dict,
    fetch_interval: int | None = None,
) -> str:
    """Add a news source. `source_type` is one of rss, atom, reddit, email,
    mastodon, arxiv, lemmy, github, bluesky, telegram, scraper. `config` is
    type-specific: rss/atom take {"url": ...}, reddit {"subreddit": ...},
    arxiv {"query": ...}. For a plain website with no feed, call
    suggest_scraper_config first."""
    return _call("add_source", name=name, source_type=source_type, config=config,
                 fetch_interval=fetch_interval)


@mcp.tool()
def update_source(
    id: str,
    name: str | None = None,
    config: dict | None = None,
    is_active: bool | None = None,
    fetch_interval: int | None = None,
) -> str:
    """Rename a source, change its config, pause/resume it, or change its
    fetch interval. Only the fields you pass are changed."""
    return _call("update_source", id=id, name=name, config=config,
                 is_active=is_active, fetch_interval=fetch_interval)


@mcp.tool()
def delete_source(id: str) -> str:
    """Permanently delete a source and its articles. Confirm with the user
    first -- this cannot be undone."""
    return _call("delete_source", id=id)


@mcp.tool()
def fetch_source(id: str) -> str:
    """Fetch one source immediately, rather than trigger_fetch's
    every-source sweep. Use after adding a source to confirm it works."""
    return _call("fetch_source", id=id)


@mcp.tool()
def trigger_fetch() -> str:
    """Fetch every active source now instead of waiting for the 5-minute
    cycle."""
    return _call("trigger_fetch")


@mcp.tool()
def list_shared_sources() -> str:
    """List sources other users on this instance have made shareable."""
    return _call("list_shared_sources")


@mcp.tool()
def suggest_scraper_config(url: str) -> str:
    """Inspect a page and suggest CSS selectors for a `scraper` source. Use
    for sites with no RSS feed, then pass the result to add_source."""
    return _call("suggest_scraper_config", url=url)


@mcp.tool()
def export_sources() -> str:
    """Export every source as JSON, for backup or moving instances."""
    return _call("export_sources")


# ── Categories ──────────────────────────────────────────────────────────────

@mcp.tool()
def list_categories() -> str:
    """List categories with their keywords and article counts."""
    return _call("list_categories")


@mcp.tool()
def add_category(
    name: str,
    keywords: list[str] | None = None,
    color: str | None = None,
    prompt: str | None = None,
) -> str:
    """Create a category. Categories gate what the LLM bothers to summarize:
    classification runs first, and an article matching no category never gets
    an abstract generated."""
    return _call("add_category", name=name, keywords=keywords, color=color, prompt=prompt)


@mcp.tool()
def update_category(
    id: str,
    name: str | None = None,
    keywords: list[str] | None = None,
    color: str | None = None,
    prompt: str | None = None,
    is_active: bool | None = None,
) -> str:
    """Rename a category, change its keywords/color/prompt, or deactivate
    it. Only the fields you pass are changed."""
    return _call("update_category", id=id, name=name, keywords=keywords,
                 color=color, prompt=prompt, is_active=is_active)


@mcp.tool()
def delete_category(id: str) -> str:
    """Delete a category. Confirm with the user first."""
    return _call("delete_category", id=id)


# ── Podcasts ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_podcast_shows() -> str:
    """List podcast shows with schedule, language, and public feed URL."""
    return _call("list_podcast_shows")


@mcp.tool()
def list_podcast_episodes(page_size: int = 10) -> str:
    """List generated episodes, newest first: status, duration, and
    shownote story titles."""
    return _call("list_podcast_episodes", page_size=page_size)


@mcp.tool()
def generate_podcast_episode(show_id: str) -> str:
    """Queue an episode for a show now, instead of waiting for its daily
    schedule. Returns once queued; generation takes minutes, so poll
    list_podcast_episodes for status."""
    return _call("generate_podcast_episode", show_id=show_id)


@mcp.tool()
def get_podcast_feed_url(show_id: str, enable: bool = False) -> str:
    """Get a show's public RSS URL for a podcast app, enabling it if asked.
    The resulting link is UNAUTHENTICATED -- anyone holding it can fetch the
    audio -- so it refuses to enable without enable=true."""
    return _call("get_podcast_feed_url", show_id=show_id, enable=enable)


# ── Trends ──────────────────────────────────────────────────────────────────

@mcp.tool()
def keyword_momentum(direction: str = "rising", limit: int = 15) -> str:
    """Which topics are gaining or losing ground -- answers "what's rising
    this month?" without needing to know what to look for. `direction` is
    rising or falling. Flags newcomers and newly dormant keywords."""
    return _call("keyword_momentum", direction=direction, limit=limit)


@mcp.tool()
def keyword_trend(topics: list[dict], days: int | None = None) -> str:
    """Day-by-day coverage counts for keywords already in mind. Each topic is
    {"label": str, "keywords": [str]} and OR-matches its keywords, so one
    topic can be a synonym group. Omit `days` for all time. Use
    keyword_momentum instead to discover topics."""
    return _call("keyword_trend", topics=topics, days=days)


def main() -> None:
    # After registration, so every tool exists before any is removed.
    _apply_scope_filter()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
