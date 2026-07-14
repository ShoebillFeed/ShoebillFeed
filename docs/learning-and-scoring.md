# Learning & Scoring

Shoebill's feed ranking is driven entirely by your own feedback — never by
an engagement-optimizing algorithm, and never hidden from you. This page
explains the actual math, and where to see and adjust it.

## Category weights

Marking an item "relevant" (👍) nudges its categories' weights up;
ignoring (leaving unread while shown, or explicitly disliking) nudges them
down. The weight formula is logarithmic, so early feedback matters more
than the hundredth star on an already-favored category:

```{code-block} text
weight = max(0, base + log(1 + starred_count) * multiplier
                     - log(1 + ignored_count) * ignore_penalty)
```

- `base` (default `1.0`) — the neutral starting weight
- `multiplier` (default `0.5`) — how strongly starring boosts a category
- `ignore_penalty` (default `0.0`, configurable) — how strongly being
  shown-but-ignored suppresses a category
- An optional `learning_window_days` setting limits the count to recent
  activity, so a category you cared about a year ago but not anymore
  doesn't stay artificially boosted forever.

This is recomputed from the current counts each time — it doesn't
compound indefinitely, so it always reflects your actual recent behavior
rather than accumulating forever.

## Keyword weights

Independent of category weights, individual **keywords** extracted from
articles you star also build up weight (same logarithmic growth), both
globally per-user and per-category-combination. Disliking an item applies
a multiplicative penalty (default ×0.8, floor 0.1) to its keywords'
weights instead.

Keywords are normalized before being compared or stored — lowercased and
lemmatized, so "interest rates" and "interest rate" collapse to the same
learned entry rather than splitting your feedback across near-duplicate
keys.

## Manual overrides

Every category also has a **manual weight**, independent of the learned
one:

| Manual weight | Effect |
|---|---|
| `0` | Muted — the category is excluded from ranking entirely |
| `1` (default) | Normal — ranking uses the learned weight as-is |
| `2` | Boosted — the learned weight is doubled |

The **Learning** panel in Settings shows, per category: the learned
weight, the manual override, the resulting effective weight, and how many
items you've starred in that category — so the ranking is always
inspectable, never a black box.

## Decay

All learned weights decay slowly over time (daily, per-user, if
`weight_decay_days` is set) — a multiplicative daily factor computed so
that a single like's worth of weight decays back to neutral over roughly
that many days. Rows that decay below a negligible threshold are pruned
outright rather than left cluttering the learned-weight tables. Decay uses
bulk SQL `UPDATE`/`DELETE` rather than loading and saving each row
individually through the ORM, specifically to avoid `StaleDataError` under
concurrent writes at scale.

## Feed diversity

Beyond raw ranking, the feed applies per-category and per-source caps (so
one prolific category or source can't crowd out everything else) plus a
small "exploration budget" — a fraction of slots reserved for
lower-ranked items, so a category that's fallen out of favor still gets
occasional exposure rather than disappearing from the feed permanently
once its weight drops.

## Keyword clusters

Related learned keywords (e.g. "llm", "large language model", "gpt-4")
are periodically grouped into keyword clusters (a daily background job),
shown in Settings as a way to see, at a glance, which topic clusters
you're actually gravitating toward over time.
