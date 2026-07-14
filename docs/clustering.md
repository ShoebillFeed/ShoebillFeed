# Clustering

When multiple sources cover the same story, Shoebill groups them into one
cluster: one card, one synthesized summary, with each source's unique
contribution called out — rather than five near-identical headlines
competing for your attention. Clustering runs in two passes.

## First pass: title similarity (at fetch time)

As soon as new items are fetched, their titles are compared using Jaccard
similarity over normalized, stop-word-filtered title words:

- A minimum of 2 shared significant words *and* a similarity ratio above
  threshold are both required — a single coincidentally-shared word
  (a recurring name, a leftover year) isn't enough on its own.
- New items are compared against each other, and against items fetched in
  the last 48 hours, scoped to the same user (clustering never crosses
  user boundaries, even when two users share a fanned-out source — see
  {doc}`architecture`).
- Joining an *existing* cluster requires matching that cluster's combined
  title vocabulary across all its members, not just one (possibly
  tangential) member — this stops a new item "drifting" into a
  long-running cluster via a single weak link.

## Second pass: after LLM processing

Items that stayed standalone after the first pass get a second chance
once they've been individually processed and have an embedding:

1. **Embedding cosine distance** (primary) — a pgvector nearest-neighbor
   search against other recently-processed items, using the
   `nomic-embed-text` embedding generated during LLM processing (see
   {doc}`llm-providers`). Fast, and captures semantic similarity that
   doesn't share any title words at all.
2. **Keyword Jaccard** (fallback) — used if no embedding is available, or
   no embedding match is found: compares extracted keywords the same way
   the first pass compares title words, with the same anti-drift
   safeguard against a cluster's overall keyword vocabulary. (The
   embedding path skips this extra check, since cosine distance already
   captures holistic content similarity.)

## What happens once items are clustered

`process_cluster` sends every member's title and content to the LLM in a
single call — deduplicating identical content first to save tokens — and
gets back:

- One unified title and summary (the "common ground" across all sources)
- A short note per source on what it uniquely adds beyond the others
  (a specific fact, quote, or angle not present elsewhere) — shown when
  you expand a cluster's source list
- Combined keywords, category, and relevance/impact scores for the
  cluster as a whole

Adding a new item to an existing cluster resets its `llm_processed` flag,
so the cluster gets reprocessed with the new member's content folded in.
