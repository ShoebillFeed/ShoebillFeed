# Introduction

## What is Shoebill Feed?

Shoebill Feed is a free, open-source news reader you run yourself — on your
own computer, a home server, or a small cloud instance. Instead of an
algorithm tuned to keep you scrolling, it collects news only from the
sources you choose and organizes it around what you actually read and like.

## Core ideas

- **You choose the sources.** RSS/Atom feeds, subreddits, email
  newsletters, Mastodon/Lemmy/Bluesky accounts and hashtags, GitHub
  releases, Telegram channels, arXiv searches, or a generic scraper for
  sites without a feed. Nothing appears in your feed that you didn't
  deliberately add. See {doc}`sources`.
- **LLM-powered processing.** Every article gets a plain-language summary,
  extracted keywords, a category assignment, and relevance/impact scores —
  via either a local model (Ollama) or a cloud provider (Anthropic), your
  choice. See {doc}`llm-providers`.
- **Learns from your feedback, not from ads.** A 👍/👎 on an article
  quietly reshapes how your feed is ranked over time, using nothing but
  your own signal. Every learned weight is visible and adjustable — never
  a black box. See {doc}`learning-and-scoring`.
- **Related coverage, grouped.** When several sources cover the same
  story, Shoebill clusters them into one card with a synthesized summary
  of the common ground, instead of showing the same headline five times.
  See {doc}`clustering`.
- **Multi-user.** Separate accounts, separate feeds, separate learned
  preferences, all on one instance.

## What it isn't

Shoebill Feed doesn't try to keep you reading inside the app. Summaries
exist to help you decide what's worth your time — the actual article is
always read on the original site, via an outbound link. It's a triage
tool, not a replacement for the sources it aggregates.

## License

Shoebill Feed is licensed under the [GNU Affero General Public License
v3.0](https://www.gnu.org/licenses/agpl-3.0.html) (AGPLv3) — the same
license Nextcloud uses, chosen specifically so that anyone hosting a
modified version keeps their changes open too.
