#!/usr/bin/env python3
"""Shoebill Feed MCP Server.

Exposes your Shoebill Feed instance as an MCP tool server so Claude and other
MCP clients can read, search, and interact with your personal news feed.

Configuration (environment variables):
  SHOEBILL_API_URL    Base URL of the Shoebill API, e.g. http://localhost:8000/api
  SHOEBILL_API_TOKEN  API token generated in Settings → Preferences → API Tokens

Run with:
  uv run --with mcp --with httpx server.py
  # or after: pip install mcp httpx
  python server.py
"""

import os
import sys
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


def _fmt_item(item: dict) -> str:
    lines = []
    if item.get("title"):
        lines.append(f"**{item['title']}**")
    cats = ", ".join(c["name"] for c in item.get("categories", []))
    if cats:
        lines.append(f"Categories: {cats}")
    if item.get("abstract"):
        lines.append(item["abstract"])
    if item.get("url"):
        lines.append(f"URL: {item['url']}")
    meta = []
    if item.get("source"):
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
    lines.append(f"ID: {item['id']}")
    return "\n".join(lines)


server = Server("shoebill-feed")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_feed",
            description=(
                "Get news items from the feed. Returns the most recent articles, "
                "optionally filtered by tab or read status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tab": {
                        "type": "string",
                        "description": "Feed tab: 'newest', 'relevant', or 'impact'. Defaults to 'newest'.",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of items to return (1–50, default 20).",
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "If true, return only unread articles.",
                    },
                },
            },
        ),
        types.Tool(
            name="search_news",
            description="Search news articles by keyword across title, abstract, and content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results (1–50, default 20).",
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
                    "id": {"type": "string", "description": "Article ID (UUID)."},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="mark_read",
            description="Mark a news article as read (if not already read).",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="mark_unread",
            description="Mark a news article as unread (if currently read).",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID."}},
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
                "properties": {"id": {"type": "string", "description": "Article ID."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="dislike",
            description="Dislike a news article to downgrade similar future articles.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="bookmark",
            description="Add a news article to Read Later.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID."}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="unbookmark",
            description="Remove a news article from Read Later.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Article ID."}},
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
        params: dict = {"tab": tab, "page_size": page_size}
        if args.get("unread_only"):
            params["is_read"] = False
        data = _get("/news", params)
        items = data.get("items", [])
        if not items:
            return "No items found."
        return "\n\n---\n\n".join(_fmt_item(i) for i in items)

    if name == "search_news":
        query = args["query"]
        page_size = min(int(args.get("page_size", 20)), 50)
        items = _get("/news/search", {"q": query, "page_size": page_size})
        if not items:
            return f"No results for '{query}'."
        return f"Results for '{query}':\n\n" + "\n\n---\n\n".join(_fmt_item(i) for i in items)

    if name == "get_item":
        item = _get(f"/news/{args['id']}")
        lines = [_fmt_item(item)]
        if item.get("raw_content"):
            lines.append(f"\nContent:\n{item['raw_content'][:3000]}")
        return "\n".join(lines)

    if name == "mark_read":
        item = _get(f"/news/{args['id']}")
        if not item.get("is_read"):
            _patch(f"/news/{args['id']}/read")
        return "Marked as read."

    if name == "mark_unread":
        item = _get(f"/news/{args['id']}")
        if item.get("is_read"):
            _patch(f"/news/{args['id']}/read")
        return "Marked as unread."

    if name == "mark_all_read":
        _post("/news/mark-all-read")
        return "All items marked as read."

    if name == "like":
        _patch(f"/news/{args['id']}/relevant")
        return "Liked."

    if name == "dislike":
        _patch(f"/news/{args['id']}/dislike")
        return "Disliked."

    if name == "bookmark":
        item = _get(f"/news/{args['id']}")
        if not item.get("read_later"):
            _patch(f"/news/{args['id']}/read-later")
        return "Added to Read Later."

    if name == "unbookmark":
        item = _get(f"/news/{args['id']}")
        if item.get("read_later"):
            _patch(f"/news/{args['id']}/read-later")
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
            lines.append(f"{active} {s['name']} ({s.get('source_type', 'unknown')})")
        return "\n".join(lines)

    if name == "list_categories":
        cats = _get("/categories")
        if not cats:
            return "No categories."
        lines = []
        for c in cats:
            active = "✓" if c.get("is_active") else "✗"
            lines.append(f"{active} {c['name']}")
        return "\n".join(lines)

    if name == "trigger_fetch":
        _post("/sources/fetch-all")
        return "Fetch triggered. New articles will appear within a minute."

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
