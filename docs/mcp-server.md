# MCP Server

`mcp_server/` is a standalone [Model Context Protocol](https://modelcontextprotocol.io/)
server that exposes a running Shoebill instance to Claude (or any other
MCP client) — letting an AI assistant read, search, and interact with
your personal feed on your behalf. It's independent of the main Docker
Compose stack; it talks to your instance purely over its regular REST API.

## Setup

1. Generate an API token: **Settings → Preferences → API Tokens** in the
   web UI (see {doc}`user-guide`).
2. Run the server:

   ```bash
   cd mcp_server
   SHOEBILL_API_URL=http://localhost:8000/api \
   SHOEBILL_API_TOKEN=<your token> \
   uv run --with mcp --with httpx server.py
   ```

   or, without `uv`:

   ```bash
   pip install mcp httpx
   SHOEBILL_API_URL=http://localhost:8000/api SHOEBILL_API_TOKEN=<your token> python server.py
   ```

| Variable | Default | Description |
|---|---|---|
| `SHOEBILL_API_URL` | `http://localhost:8000/api` | Base URL of your Shoebill instance's API |
| `SHOEBILL_API_TOKEN` | — | Required — the server exits immediately if unset |

Authentication is a `Bearer` token on every request, the same
per-user API token mechanism described in {doc}`user-guide`  — no
separate credentials, and access is scoped to whatever that token's owner
can already see.

## Connecting it to Claude

Add it as an MCP server in your client's configuration, pointing at
`mcp_server/server.py` with the two environment variables above set. Once
connected, Claude can query your feed, search items, and take the same
actions (mark read, star, etc.) a logged-in user could — useful for
things like "summarize what's new in my Technology category today" or
"find that article about X I read last week."
