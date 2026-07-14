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

## Stats

A per-user activity view: items fetched/read/starred over time, and a
breakdown of your reading activity by category.

## Admin: Users

Admin accounts can create additional user accounts, reset passwords, and
view aggregate usage stats across all users, under **Settings → Users**.
