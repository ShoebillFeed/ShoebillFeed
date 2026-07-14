# Sources

A **source** is one feed of content: an RSS feed, a subreddit, an arXiv
search, and so on. Each source has a `source_type` and a `config` object
whose shape depends on the type. This page documents every supported type.

All sources share two common fields regardless of type:

| Field | Default | Notes |
|---|---|---|
| `fetch_interval` | `3600` seconds | Minimum `300` (5 minutes). The settings UI only offers fixed choices (15m / 30m / 1h / 6h / 24h), but the API accepts any integer ≥ 300. |
| `is_active` | `true` | Inactive sources are skipped by the fetch scheduler. |

Sources with an identical `(source_type, config)` pair across different
users are fetched once per cycle and fanned out to every subscriber — see
{doc}`architecture`.

## RSS / Atom

```{code-block} json
{"url": "https://example.com/feed.xml"}
```

`url` is the only field. If it points at an HTML page rather than a raw
feed, Shoebill tries to autodiscover a feed link on that page. `atom` is
handled by the same fetcher as `rss` — there's no configuration
difference between the two types.

## Reddit

```{code-block} json
{
  "subreddit": "MachineLearning",
  "sort": "hot",
  "limit": "25"
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `subreddit` | yes | — | No `r/` prefix |
| `sort` | no | `hot` | |
| `limit` | no | `25` | |
| `client_id` / `client_secret` | no | — | Per-source Reddit API credentials. Falls back to the global `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` env vars if omitted; a per-source value takes priority over the global one. |
| `username` / `password` | no | — | Only needed for the OAuth "password" grant (script-type Reddit apps); without them, Shoebill authenticates as `client_credentials` (app-only). |

Adding a Reddit source in the UI auto-fills the credential fields from any
Reddit source you've already configured, so you only enter your API
credentials once even when adding several subreddits.

## Email (IMAP newsletters)

```{code-block} json
{
  "imap_host": "imap.example.com",
  "imap_port": "993",
  "username": "you@example.com",
  "password": "...",
  "folder": "INBOX",
  "subject_filter": "Weekly Digest"
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `imap_host` | yes | — | |
| `username` / `password` | yes | — | Plain IMAP auth over `IMAP4_SSL` — no OAuth2 support |
| `imap_port` | no | `993` | |
| `folder` | no | `INBOX` | |
| `subject_filter` | no | — | Plain IMAP `SUBJECT` search string, not a filter language |

Each matching email is treated as a "newsletter wrapper" — the LLM
extracts the individual articles it contains and creates one `NewsItem`
per article (see {doc}`llm-providers`).

```{warning}
The `password` field takes any password, including your real account
password. There's no built-in distinction between a full account password
and an app-specific password. **Use an app password** (most providers —
Gmail, Fastmail, etc. — support generating one) rather than your real
account password, since it's stored so the fetcher can use it on every
poll.
```

## Mastodon

```{code-block} json
{"instance_url": "mastodon.social", "feed_type": "hashtag", "name": "opensource"}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `instance_url` | yes | — | Scheme is added automatically if omitted |
| `feed_type` | no | `hashtag` | `user`, `hashtag`, or `local` |
| `name` | required unless `feed_type=local` | — | Account name (for `user`) or hashtag (for `hashtag`), without `@`/`#` |

Uses each instance's built-in RSS endpoints (`/@user.rss`, `/tags/x.rss`,
`/public/local.rss`) rather than the Mastodon API — no auth needed.

## Bluesky

```{code-block} json
{"feed_type": "user", "handle": "bsky.app", "limit": "20"}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `feed_type` | no | `user` | `user` or `search` |
| `handle` | required for `feed_type=user` | — | Leading `@` is stripped automatically |
| `query` | required for `feed_type=search` | — | |
| `limit` | no | `20` | Capped at 100 |

Uses the public AT Protocol AppView API — no authentication required.

## Lemmy

```{code-block} json
{"instance_url": "lemmy.world", "community": "technology", "sort": "Hot", "limit": "25"}
```

| Field | Required | Default |
|---|---|---|
| `instance_url` | yes | — |
| `community` | yes | — |
| `sort` | no | `Hot` (`Hot`, `New`, `TopDay`, `TopWeek`) |
| `limit` | no | `25` |

## GitHub

Two modes, chosen via `mode`:

```{code-block} json
{"mode": "releases", "repo": "openai/openai-python", "limit": "20"}
```

```{code-block} json
{"mode": "trending", "language": "python", "since": "daily"}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `mode` | no | `releases` | `releases` or `trending` |
| `repo` | required for `releases` | — | `"owner/repo"` |
| `limit` | no | `20` | Capped at 100 |
| `token` | no | — | A GitHub PAT, for higher API rate limits |
| `prerelease` | no | `false` | Include prereleases; `"true"`/`"false"` string |
| `language` | no | all languages | For `trending` mode |
| `since` | no | `daily` | For `trending` mode: `daily`, `weekly`, `monthly` |

## arXiv

```{code-block} json
{"query": "transformer architecture"}
```

`query` is the only field — searches arXiv's official Atom API directly
(not Google Scholar, despite this fetcher historically also being
reachable under a `"scholar"` type name — that legacy alias has since
been removed; any existing sources that used it were migrated to
`"arxiv"` automatically).

## Telegram

```{code-block} json
{"channel": "durov"}
```

`channel` (no `@` prefix) is the only field. Scrapes the public
`t.me/s/{channel}` web preview; channels without a public preview fail
gracefully (empty result, logged warning) rather than erroring.

## Generic scraper

For sites with no feed at all:

```{code-block} json
{
  "url": "https://example.com/news",
  "item_selector": "article.post",
  "title_selector": "h2",
  "link_selector": "a",
  "content_selector": ".post-body",
  "fetch_full_articles": "true"
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `url` | yes | — | |
| `item_selector` | yes | — | CSS selector matching each article's container element |
| `title_selector` | no | `h1,h2,h3` | |
| `link_selector` | no | `a` | |
| `content_selector` | no | — | Falls back to the full container's text if omitted |
| `base_url` | no | = `url` | For resolving relative links |
| `fetch_full_articles` | no | `true` | Follow each article's link to fetch the full text when the listing excerpt is under 300 characters |

`robots.txt` is checked both when the source is created and on every
subsequent fetch — a scraper source can't be created against a site whose
`robots.txt` disallows it.

**Auto-detect selectors**: rather than writing CSS selectors by hand, the
"Auto-detect" button in the source form calls the configured LLM to
propose them — it fetches the page, strips it to a simplified
tag/class/href skeleton, asks the LLM for `item_selector` /
`title_selector` / `link_selector` / `content_selector`, validates the
result by actually running the selectors against the page, and retries
once if the first attempt matches zero items.
