# Changelog

## 1.3.0

Largely an MCP release: the server that exposes your feed to Claude went
from 14 tools to 33, gained per-token permissions, and picked up its first
test suite. Alongside that, several Ollama failure modes that reported
success are now caught, and article processing switched to newest-first.

### MCP server

- **19 new tools** (14 → 33), covering the learning profile, source and
  category curation, podcasts, and keyword trends. An assistant can now
  answer "why is this at the top of my feed?", correct a preference that
  was learned by accident, add a feed and a category for it, generate a
  podcast episode, or report what's rising this month.
- **Actions work on multi-source stories.** Clustered stories were
  rendered identically to single articles, so liking or bookmarking one
  aimed at the wrong API route and silently did nothing — on exactly the
  stories most worth acting on. Cluster IDs are now shown as
  `cluster:<uuid>`; pass them back verbatim. Their summaries and member
  outlets display too, neither of which appeared before.
- **Per-token permissions.** A token can be limited to any subset of
  `read`, `act`, `curate`, `learning`, `podcasts` and `stats`, chosen with
  checkboxes in Settings → Preferences → API Tokens. Hand a read-only
  token to one client and a full one to another; revoking either is just
  deleting that token.
- **Requires `mcp>=2`** — see Upgrading.
- First test suite (38 tests) and CI workflow; previously neither existed.

### Reliability

- **Ollama health checks no longer pass when the model is missing.** A
  reachable daemon that never pulled `OLLAMA_MODEL` reported healthy while
  every real call returned 404. Piper likewise only checked that its voice
  directory was writable, which says nothing about whether it can
  synthesize.
- **Fixed silent empty responses from some Ollama models.** Certain
  thinking models (confirmed with `qwen3:4b`) return the answer in the
  response's `thinking` field and leave `response` empty. Nothing errored,
  so every article was handed an empty string to parse.
- **`ollama-init` pulls the model you configured**, not a hardcoded one, so
  changing `OLLAMA_MODEL` no longer brings the stack up with the model
  absent. It also pulls the embedding model, which nothing pulled before.
- **The embedding model stays resident between batches** instead of
  expiring after five minutes and reloading on the next run.
- Celery services have healthchecks, so a hung worker restarts itself.

### Feed and processing

- **Newest articles are processed first.** The 15-minute sweep previously
  selected with no ordering at all, so under a backlog which articles got
  processed was effectively arbitrary. Note the tradeoff: if articles
  arrive faster than they can be processed for long enough, the oldest stop
  being picked up. A persistently growing unprocessed count is the signal.
- **arXiv papers keep their own subject categories.** arXiv's curated tags
  (`cs.LG`, `quant-ph`) are translated to readable labels and merged with
  the LLM's keywords — steadier clustering signal than inferred wording
  alone.

### Interface

- Settings → LLM shows **how many requests each model handled** in the last
  hour and day, lists the podcast TTS engine as a configured provider, and
  opens with its panels expanded and the health check already run.
- The keyword cluster map no longer shifts the page as you hover between
  clusters.

### Upgrading

- **Two migrations** (`0056`, `0057`) apply automatically when the backend
  starts. No manual step.
- **If you run the MCP server, reinstall its dependencies.** It now needs
  `mcp>=2`, which replaced the API the server was built on. Use
  `uv run --with 'mcp>=2' --with httpx server.py`, or
  `pip install -r mcp_server/requirements.txt`.
- **Existing API tokens keep working unchanged**, with no restrictions.
  Permissions are opt-in per token, and only apply to tokens — your own
  browser session is never limited.
- Processing order changed, as described above.
