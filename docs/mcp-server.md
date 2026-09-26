# MCP Server

`mcp_server/` is a standalone [Model Context Protocol](https://modelcontextprotocol.io/)
server that exposes a running Shoebill instance to Claude (or any other
MCP client) — letting an AI assistant read, search, and interact with
your personal feed on your behalf. It's independent of the main Docker
Compose stack; it talks to your instance purely over its regular REST API.

## Setup

1. Generate an API token: **Settings → Preferences → API Tokens** in the
   web UI (see {doc}`user-guide`). Tick only the permissions the client
   actually needs — see [Permissions](#permissions) below.
2. Run the server:

   ```bash
   cd mcp_server
   SHOEBILL_API_URL=http://localhost:8000/api \
   SHOEBILL_API_TOKEN=<your token> \
   uv run --with 'mcp>=2' --with httpx server.py
   ```

   or, without `uv`:

   ```bash
   pip install -r requirements.txt
   SHOEBILL_API_URL=http://localhost:8000/api SHOEBILL_API_TOKEN=<your token> python server.py
   ```

| Variable | Default | Description |
|---|---|---|
| `SHOEBILL_API_URL` | `http://localhost:8000/api` | Base URL of your Shoebill instance's API |
| `SHOEBILL_API_TOKEN` | — | Required — the server exits immediately if unset |

```{note}
The `mcp>=2` pin is load-bearing. The server is built on `MCPServer`, which
replaced the low-level `Server` class and its `@server.list_tools()` /
`@server.call_tool()` decorators in mcp 2.0. Installing an unpinned `mcp`
alongside an older checkout — or a 1.x `mcp` with a current one — fails at
import with `AttributeError: 'Server' object has no attribute 'list_tools'`.
```

Authentication is a `Bearer` token on every request, the same per-user API
token mechanism described in {doc}`user-guide`.

(permissions)=
## Permissions

A token can be limited to a subset of capabilities. Tick the boxes when
creating it; leaving all of them ticked creates an unrestricted token,
which is also what every token generated before this feature existed
remains.

| Scope | Allows |
|---|---|
| `read` | Read the feed, articles, sources and categories |
| `act` | Mark read, like, dislike and bookmark articles |
| `curate` | Add, edit and delete sources and categories |
| `learning` | View and adjust learned interest weights |
| `podcasts` | List shows and episodes, and generate episodes |
| `stats` | Read statistics and keyword trends |

Scopes are enforced by the **API**, not by this server. That distinction
matters: the MCP server is just a client holding a token, so a restriction
that only hid tools here could be bypassed by calling the REST API directly
with the same token. On startup the server asks the API what its own token
may do and hides the tools it can't use, purely so the model isn't offered
something that would fail — the actual boundary is server-side and applies
either way.

Two consequences worth knowing:

- **API tokens can never manage API tokens.** `/api/tokens` and `/api/auth`
  are closed to token authentication at any scope, unrestricted included —
  otherwise a token could mint itself a broader one and outlive its own
  revocation. Manage tokens from the web UI.
- **Scopes limit a token, not a user.** Your own browser session is never
  scope-limited.

## What Claude can do

33 tools, grouped by the scope they need:

- **`read`** — `get_feed`, `search_news`, `get_item`, `get_digest`,
  `list_sources`, `list_categories`, `list_shared_sources`
- **`act`** — `mark_read`, `mark_unread`, `mark_all_read`, `like`,
  `dislike`, `bookmark`, `unbookmark`
- **`curate`** — `add_source`, `update_source`, `delete_source`,
  `fetch_source`, `trigger_fetch`, `suggest_scraper_config`,
  `export_sources`, `add_category`, `update_category`, `delete_category`
- **`learning`** — `get_learning_profile`, `set_category_weight`,
  `forget_keyword`
- **`podcasts`** — `list_podcast_shows`, `list_podcast_episodes`,
  `generate_podcast_episode`, `get_podcast_feed_url`
- **`stats`** — `keyword_momentum`, `keyword_trend`

```{note}
Feed entries come in two kinds. A standalone article's ID is a plain UUID;
a multi-source story (a cluster — see {doc}`clustering`) is shown as
`cluster:<uuid>`. Pass whichever you were given back verbatim: the prefix is
how the tools know to act on the cluster rather than looking for an article
that doesn't exist.
```

Some tools are deliberately cautious. `get_podcast_feed_url` will not
enable a show's public feed unless you pass `enable=true`, because that
produces an **unauthenticated** URL that anyone holding it can use to fetch
your audio.

## Connecting it to Claude

Add it as an MCP server in your client's configuration, pointing at
`mcp_server/server.py` with the two environment variables above set. Once
connected, Claude can handle things like "summarize what's new in my
Technology category today", "find that article about X I read last week",
"why is this at the top of my feed?", "add an RSS feed for X and a category
for it", or "what topics are rising this month?"
