# User Guide

## The feed

The main feed has several tabs (Newest, Relevant, Impact, Read Later,
plus any custom tabs you define) and can be filtered by category, by
source, to unread-only, or to uncategorized-only. Each card shows:

- A pill per source (one per outlet, for a clustered story — see
  {doc}`clustering`) and a category pill
- The LLM-generated title/summary, with an info icon showing which
  provider and model produced it (see {doc}`llm-providers`)
- 👍/👎 to mark relevant/disliked (feeds {doc}`learning-and-scoring`),
  plus bookmark (read later) and share actions

Clicking a card's title opens the original article on the source site —
Shoebill only ever shows a summary and a link out (see
{doc}`introduction`).

**Custom tabs** let you save a specific combination of filters (a
category, a source, a sort order) as a named, one-click tab — useful for
"just my work-relevant categories" or "just this one source" views you
switch to often.

## Podcast

**Podcasts** (top-level nav, next to Feed) is where generated episodes
appear, each with an inline audio player, a status badge
(queued/generating/ready/failed), and an expandable transcript. A ready or
failed episode also has a **regenerate** button (circular arrow icon) that
re-runs generation for that same episode — useful if you weren't happy
with how it turned out, or if it failed and you want to retry. This
replaces its script and audio; the episode's link stays the same, so
anything that already pointed at it (e.g. a podcast app that cached the
episode URL) keeps working once the new version is ready.

Configure shows under **Settings → Podcast**: a name, an optional show
concept/description, up to three hosts (each with a name, a free-text
character prompt describing their personality, and a voice), which
categories and feeds to draw stories from (empty = all), a time window, a
target length (up to 15 minutes), a language, a speech speed, a cover
image, and a daily generation time plus timezone. "Generate now" triggers
an episode immediately instead of waiting for the schedule.

The show concept shapes *what* the episode covers and its overall
angle (e.g. "focus on market impact, skeptical tone, skip celebrity
gossip"), on top of each host's own character prompt, which shapes how
*that host's* lines are written — tone, vocabulary, personality. Neither
changes how the voice *sounds*. Voices are rendered by a pluggable
text-to-speech engine — [Piper](https://github.com/OHF-Voice/piper1-gpl)
(self-hosted, offline) by default, or Kokoro/Chatterbox if the server
operator has set up a network TTS backend — so two hosts sharing the only
voice available for a language will sound identical even with very
different character prompts. Click the play icon next to a host's voice
picker to hear a short sample before committing to it.

Speech speed (0.75x–1.5x) adjusts how fast a voice talks, but not every
engine supports it — Chatterbox has no speed control at all, and the form
tells you when the configured engine can't honor it rather than leaving
the slider silently doing nothing. If the engine is Chatterbox, hosts also
get an **emotion intensity** control (delivery/expressiveness, not
available on Piper or Kokoro). If the server has a second TTS engine
configured alongside the default, each host can also be pinned to a
specific **voice engine** independently — e.g. one host on the default
local voice, another on a more expressive network one — via a selector
that only appears once a second engine is actually available to choose
from.

Each ready episode shows **show notes**: one entry per story actually
covered, with a clickable timestamp that jumps the player to where that
story starts and a link to the original source article. The same
timestamps are published as podcast chapter markers (the
[Podcasting 2.0 namespace](https://podcastindex.org/namespace/1.0)'s
`<podcast:chapters>`) in the RSS feed, so podcast apps that support
chapters show the same jump-to-story markers there too.

If a single line of dialogue fails to synthesize (a transient error, e.g.
a momentary blip talking to a network TTS backend), Shoebill retries it a
few times before giving up on just that one line rather than failing the
whole episode.

### Listening in a podcast app

Each show has an RSS feed icon next to it in **Settings → Podcast**. Click
it, then "Enable link" to generate a private feed URL — add that URL
directly in Apple Podcasts, Overcast, Pocket Casts, or any other podcast
app, no login required. This requires the server to have `PUBLIC_BASE_URL`
configured (see {doc}`configuration`); if it isn't, enabling shows an
error explaining that.

The link only works while the feed is enabled and only exposes that one
show's ready episodes — nothing else in your account. "Regenerate" issues
a new link and immediately invalidates the old one, useful if you shared
it somewhere you didn't mean to; apps using the old link will simply stop
getting new episodes until you update it there too. Disabling (rather than
regenerating) pauses the feed without discarding the link, so re-enabling
later restores the same URL.

## Categories

**Settings → Categories** is where you define the topics Shoebill sorts
articles into. Each category has a name, a color, optional keywords, and
an optional custom prompt fragment giving the LLM extra context on what
belongs in it. A built-in IPTC-based taxonomy of common categories is
available as a starting point, and a "Default Categories" browser lets
you pull in ones you want without hand-writing them all.

## Sources

**Settings → Sources** — add, edit, deactivate, and manually trigger a
fetch for any source. See {doc}`sources` for every source type's exact
configuration. Sources can be exported/imported as JSON, and you can copy
another user's shared source configuration directly rather than
re-entering it.

## Learning

**Settings → Learning** shows every category's learned weight, manual
override, and effective weight, plus how many items you've starred in
each — see {doc}`learning-and-scoring` for exactly how these numbers are
computed. This is also where you mute (0×) or boost (2×) a category
manually.

## Preferences

Theme (light/dark), UI language, output language (if you want summaries
translated regardless of source language), and the numeric tuning
parameters behind scoring/decay/diversity (see
{doc}`learning-and-scoring`) for anyone who wants to adjust the defaults.

**API Tokens**, also under Preferences, is where you generate a token for
external tools — notably the {doc}`mcp-server`, which lets Claude or
other MCP clients read and interact with your feed.

## Notifications

Push notifications (Web Push — see {doc}`configuration` for the VAPID
setup this requires) can be scoped to a relevance threshold, specific
categories, and/or a specific custom tab, so you're only notified about
the subset of your feed you actually want interrupted for.

## Analytics

**Analytics** (top-level nav, next to Podcasts) is a per-user activity
view split into tabs:

- **Activity** — items fetched/read/liked/disliked over time.
- **Categories & Sources** — volume by category and by source, plus
  which pairs of sources most often cover the same story.
- **Trends** — how coverage of a keyword, or a loose group of
  OR-matched keywords ("topic"), has evolved day by day. Add up to six
  topics to compare on one chart, each built from your own keywords or
  imported from an existing keyword cluster (see
  {doc}`learning-and-scoring`), and optionally filter by category or
  source. A topic built from a keyword cluster shows that cluster's
  real historical coverage, not just a snapshot going forward. The
  time range goes from 7 days up to a year, or "All" for your entire
  history. "Export CSV" downloads the chart's underlying counts (one
  column per topic, one row per date). Your topics and filters are
  remembered in the browser, so they're still there next time you
  open this tab.
- **Learning** — category weight history and the keyword cluster map
  (see {doc}`learning-and-scoring`).
- **Podcast** — categories, keywords, and sources covered in each
  generated episode of a selected show.

Recording can be paused at any time from the toggle at the top of the
page; pausing stops new history from being recorded without deleting
what's already there.

## Admin: Users

Admin accounts can create additional user accounts, reset passwords, and
view aggregate usage stats across all users, under **Settings → Users**.
