#!/usr/bin/env python3
"""Shoebill Feed MCP Server.

Exposes your Shoebill Feed instance as an MCP tool server so Claude and other
MCP clients can read, search, and interact with your personal news feed.

Configuration (environment variables):
  SHOEBILL_API_URL    Base URL of the Shoebill API, e.g. http://localhost:8000/api
  SHOEBILL_API_TOKEN  API token generated in Settings → Preferences → API Tokens

Run with:
  uv run --with 'mcp<2' --with httpx server.py
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
    import mcp.server.stdio
    import mcp.types as types
    from mcp.server import Server
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


server = Server("shoebill-feed")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_feed",
            description=(
                "Get news items from the feed. Returns articles ordered by the selected sort mode, "
                "optionally filtered by read status, categories, or sources."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tab": {
                        "type": "string",
                        "description": (
                            "Sort/filter mode: 'newest' (by date), 'relevant' (by personalised score), "
                            "'impact' (by impact score), or 'read_later' (bookmarked items). Defaults to 'newest'."
                        ),
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of items to return (1–50, default 20).",
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "If true, return only unread articles.",
                    },
                    "category_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by category UUIDs (use list_categories to discover IDs).",
                    },
                    "source_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by source UUIDs (use list_sources to discover IDs).",
                    },
                },
            },
        ),
        types.Tool(
            name="search_news",
            description=(
                "Search news articles by keyword across title, abstract, and content. "
                "Supports the same sort modes and filters as the main feed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'newest' (default), 'relevant', or 'impact'.",
                    },
                    "category_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter results to these category UUIDs (use list_categories to discover IDs).",
                    },
                    "source_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter results to these source UUIDs (use list_sources to discover IDs).",
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "If true, return only unread articles.",
                    },
                    "bookmarked_only": {
                        "type": "boolean",
                        "description": "If true, return only bookmarked (Read Later) articles.",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results (1–50, default 50).",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_item",
            description="Get full details for a single news article by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="mark_read",
            description="Mark a news article as read (if not already read).",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="mark_unread",
            description="Mark a news article as unread (if currently read).",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="mark_all_read",
            description="Mark all currently visible feed items as read.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="like",
            description=(
                "Like (mark as relevant) a news article to train the feed's personalisation. "
                "Toggles the liked state."
            ),
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="dislike",
            description="Dislike a news article to downgrade similar future articles.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="bookmark",
            description="Add a news article to Read Later.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="unbookmark",
            description="Remove a news article from Read Later.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID, exactly as shown in the feed. Multi-source stories are prefixed cluster:<uuid> -- pass the whole string through unchanged."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="get_digest",
            description=(
                "Get a concise digest of today's top articles from the Relevant or Impact "
                "tab — useful for a quick briefing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "integer",
                        "description": "Number of top articles to include (default 10).",
                    },
                    "tab": {
                        "type": "string",
                        "description": "'relevant' or 'impact' (default 'relevant').",
                    },
                },
            },
        ),
        types.Tool(
            name="list_sources",
            description="List all configured news sources.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_categories",
            description="List all news categories.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="trigger_fetch",
            description=(
                "Trigger an immediate fetch cycle for all sources "
                "(normally runs every 5 minutes automatically)."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Learning profile ────────────────────────────────────────────
        types.Tool(
            name="get_learning_profile",
            description=(
                "Show what Shoebill has learned about the user's interests: per-category "
                "learned and manual weights with how many articles were marked in each, "
                "plus the top learned keyword weights. Use this to explain WHY something "
                "ranks highly in the Relevant tab, or before adjusting a preference."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="set_category_weight",
            description=(
                "Set a category's MANUAL weight multiplier (0.0-5.0). This is the "
                "user-controlled dial; it multiplies the separately learned weight rather "
                "than replacing it. 1.0 is neutral, 0.0 suppresses the category. Use when "
                "the user says a topic is over- or under-represented."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category_id": {"type": "string", "description": "Category UUID (see list_categories)."},
                    "manual_weight": {"type": "number", "description": "0.0-5.0; 1.0 is neutral."},
                },
                "required": ["category_id", "manual_weight"],
            },
        ),
        types.Tool(
            name="forget_keyword",
            description=(
                "Delete a learned keyword weight, so it stops influencing ranking. Use "
                "when a keyword was learned by accident. The keyword is normalized "
                "server-side, so surface variants resolve to the same entry."
            ),
            inputSchema={
                "type": "object",
                "properties": {"keyword": {"type": "string", "description": "Keyword to forget."}},
                "required": ["keyword"],
            },
        ),
        # ── Source curation ─────────────────────────────────────────────────
        types.Tool(
            name="add_source",
            description=(
                "Add a news source. `config` is type-specific: rss/atom take {\"url\": ...}, "
                "reddit {\"subreddit\": ...}, arxiv {\"query\": ...}, mastodon {\"instance\", \"hashtag\"}, "
                "github/lemmy/bluesky/telegram/scraper their own keys. Prefer suggest_scraper_config "
                "first for a plain website."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Display name."},
                    "source_type": {
                        "type": "string",
                        "enum": ["rss", "atom", "reddit", "email", "mastodon", "arxiv",
                                 "lemmy", "github", "bluesky", "telegram", "scraper"],
                    },
                    "config": {"type": "object", "description": "Type-specific config object."},
                    "fetch_interval": {"type": "integer", "description": "Seconds between fetches (min 300)."},
                },
                "required": ["name", "source_type", "config"],
            },
        ),
        types.Tool(
            name="update_source",
            description="Rename a source, change its config, pause/resume it, or change its fetch interval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Source UUID."},
                    "name": {"type": "string"},
                    "config": {"type": "object"},
                    "is_active": {"type": "boolean", "description": "False pauses fetching without deleting."},
                    "fetch_interval": {"type": "integer"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="delete_source",
            description="Permanently delete a source and its articles. Confirm with the user first.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Source UUID."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="fetch_source",
            description=(
                "Fetch one source immediately, instead of trigger_fetch's every-source sweep. "
                "Use after adding a source to confirm it actually returns articles."
            ),
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Source UUID."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="list_shared_sources",
            description="List sources other users on this instance have made shareable, as suggestions to subscribe to.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="suggest_scraper_config",
            description=(
                "Given a URL, inspect the page and suggest CSS selectors for a `scraper` "
                "source. Use for sites with no RSS feed, then pass the result to add_source."
            ),
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Page listing articles."}},
                "required": ["url"],
            },
        ),
        types.Tool(
            name="export_sources",
            description="Export every source as JSON, for backup or moving to another instance.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Category curation ───────────────────────────────────────────────
        types.Tool(
            name="add_category",
            description=(
                "Create a category. Categories drive what the LLM bothers to summarize: "
                "Stage 1 classification gates the expensive abstract call, so an article "
                "matching no category never gets summarized."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"},
                                 "description": "Seed keywords for matching."},
                    "color": {"type": "string", "description": "Hex like #6366f1."},
                    "prompt": {"type": "string", "description": "Optional extra guidance for the classifier."},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="update_category",
            description="Rename a category, change its keywords/color/prompt, or deactivate it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Category UUID."},
                    "name": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "color": {"type": "string"},
                    "prompt": {"type": "string"},
                    "is_active": {"type": "boolean"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="delete_category",
            description="Delete a category. Confirm with the user first.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Category UUID."}},
                "required": ["id"],
            },
        ),
        # ── Podcasts ────────────────────────────────────────────────────────
        types.Tool(
            name="list_podcast_shows",
            description="List configured podcast shows, with schedule, language, and public feed URL when enabled.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_podcast_episodes",
            description=(
                "List generated podcast episodes, newest first: status, duration, and "
                "shownote story titles."
            ),
            inputSchema={
                "type": "object",
                "properties": {"page_size": {"type": "integer", "description": "Max episodes (default 10)."}},
            },
        ),
        types.Tool(
            name="generate_podcast_episode",
            description=(
                "Queue an episode for a show right now, instead of waiting for its daily "
                "schedule. Returns once queued -- generation (LLM script + TTS) runs in "
                "the background and takes minutes; poll list_podcast_episodes for status."
            ),
            inputSchema={
                "type": "object",
                "properties": {"show_id": {"type": "string", "description": "Show UUID (see list_podcast_shows)."}},
                "required": ["show_id"],
            },
        ),
        types.Tool(
            name="get_podcast_feed_url",
            description=(
                "Get a show's public RSS URL for subscribing in a podcast app, enabling it "
                "if needed. This creates an UNAUTHENTICATED link -- anyone holding it can "
                "fetch the show's audio. Confirm with the user before enabling."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "show_id": {"type": "string", "description": "Show UUID."},
                    "enable": {"type": "boolean", "description": "Enable the feed if not already on (default false)."},
                },
                "required": ["show_id"],
            },
        ),
        # ── Trends ──────────────────────────────────────────────────────────
        types.Tool(
            name="keyword_momentum",
            description=(
                "Which topics in the feed are gaining or losing ground -- answers 'what's "
                "rising this month?' without needing to know what to look for. Ranks "
                "keywords by relative growth over weekly (8 buckets) and monthly (6 "
                "buckets) windows, and flags newcomers/dormant keywords."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["rising", "falling"], "description": "Default rising."},
                    "limit": {"type": "integer", "description": "Max keywords to report (default 15)."},
                },
            },
        ),
        types.Tool(
            name="keyword_trend",
            description=(
                "Day-by-day coverage counts for keywords you already have in mind. Each "
                "topic OR-matches its keyword list, so one topic can be a single keyword "
                "or a group of synonyms. Use keyword_momentum instead to discover topics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "description": "1-6 topics, each {label, keywords[]}.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "keywords": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["label", "keywords"],
                        },
                    },
                    "days": {"type": "integer", "description": "Lookback window; omit for all time."},
                },
                "required": ["topics"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = _handle(name, arguments)
    except httpx.HTTPStatusError as exc:
        result = f"API error {exc.response.status_code}: {exc.response.text}"
    except Exception as exc:
        result = f"Error: {exc}"
    return [types.TextContent(type="text", text=result)]


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


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
