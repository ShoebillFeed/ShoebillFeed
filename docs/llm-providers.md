# LLM Providers

Shoebill uses an LLM to summarize, categorize, and score every item. The
provider is pluggable and configured entirely via environment variables —
see {doc}`configuration`.

## Choosing a provider

```{code-block} bash
LLM_PROVIDERS=ollama            # local only
LLM_PROVIDERS=anthropic         # cloud only
LLM_PROVIDERS=ollama,anthropic  # local first, cloud fallback
```

**Ollama** (local, recommended for self-hosting): free, private, runs on
your own hardware. Install [Ollama](https://ollama.com), pull a model:

```bash
ollama pull gemma3:12b   # or qwen2.5:14b, llama3.1:8b, etc.
ollama pull nomic-embed-text
```

Or run Ollama itself in Docker via the provided compose file:

```bash
docker compose -f docker-compose.ollama.yml up -d
```

then set `OLLAMA_BASE_URL=http://ollama:11434` and connect both stacks to
the same Docker network.

**Anthropic** (cloud): no local hardware needed, generally faster and more
consistent quality. Requires `ANTHROPIC_API_KEY`.

**Fallback chains**: list multiple providers, comma-separated — the first
is primary, the rest are tried in order if it fails. Each provider gets
two attempts (with a short retry delay) before falling through to the
next.

```{note}
Changing `LLM_PROVIDERS` (or any related env var) always requires a
container restart — settings are cached for the process lifetime and the
web UI's LLM config panel is read-only, for display only.
```

## Recommended models

Every call in the pipeline (see {doc}`configuration`) is short: a
classify-only pass on ~600 characters, or a summarize pass on one
article/cluster. You don't need a large model to get good results here,
and a large model mainly costs you latency and RAM/VRAM rather than
buying much summary quality for this specific task.

### Ollama (local)

Rule of thumb for a 4-bit quantized model (Ollama's default): budget
roughly 1 GB of RAM/VRAM per billion parameters, plus a couple GB of
headroom for context and the embedding model running alongside it.

| Tier | Model | Approx. RAM/VRAM | Notes |
|---|---|---|---|
| Minimal / CPU-only | `gemma3:4b` or `qwen3:4b` | ~4-6 GB | Usable on a machine with no dedicated GPU; noticeably weaker categorization on ambiguous articles |
| **Balanced (default)** | `qwen3:8b` | ~8 GB | Shoebill's `OLLAMA_MODEL` default. Good accuracy-to-resource ratio for most self-hosted setups |
| Higher quality | `gemma3:12b` or `qwen2.5:14b` | ~12-16 GB | Noticeably better summaries and category calls; still fits a single consumer GPU (e.g. RTX 3060 12GB and up) |
| Best local quality | `qwen3:32b` or `gemma3:27b` | ~24-32 GB | Diminishing returns for this task; only worth it if the hardware is already sitting there |

Regardless of which model you pick for text generation, embeddings always
use `nomic-embed-text` (see below) — it's small (~275MB) and runs
alongside any of the above without materially changing the sizing table.

Run `ollama pull` wherever Ollama itself is actually running — on your
own host if you installed Ollama natively, or inside the `ollama`
container if you're using the provided `docker-compose.ollama.yml`
(`docker compose exec ollama ollama pull ...`):

```bash
ollama pull qwen3:8b   # or any model from the table above
ollama pull nomic-embed-text
```

### Anthropic (cloud)

`claude-haiku-4-5` (the default) is the right choice for almost every
setup: the pipeline makes many small, short calls per fetch cycle, and a
larger model (Sonnet/Opus) meaningfully increases cost without much
quality gain on 600-character classification or single-article
summarization. Consider a larger model only if you rely heavily on
**translation mode** (full-content, higher-stakes generation) and find
translation quality lacking with Haiku.

## What gets sent to the LLM

Only the article's title and content (and, for clusters, the same for
every member item) — never anything about the user beyond their active
category list, used so the LLM can suggest which categories an item
matches.

## Processing pipeline

Regular articles go through a **two-stage** pipeline, to avoid spending
tokens summarizing things nobody's categories care about:

1. **Stage 1** — a cheap classify-only call on the first 600 characters,
   with no abstract requested.
2. **Stage 2** — only runs if Stage 1 matched a category (or the user has
   no categories configured): the full-content call that produces the
   actual abstract.
3. If Stage 1 matched nothing, the raw content is used as the "abstract"
   and Stage 2 never runs.

Other branches:

- **Short items** (below `UserSettings.llm_min_word_count`, default 50
  words) skip straight to classify-only — no abstract is generated
  regardless of category match.
- **Social posts** (Mastodon/Bluesky-style) always run the full pipeline,
  and the LLM may also generate a title.
- **Translation mode** (a per-user output language set in Settings)
  always runs the full pipeline, since title and abstract both need
  translating.
- **Newsletter emails** are handled completely differently — see below.
- **Clusters** send every member item's title+content in one LLM call,
  producing one unified summary plus a short per-source note on what each
  outlet uniquely contributes (see {doc}`clustering`).

## Newsletter expansion

An `email` source's items aren't articles themselves — each fetched email
is a wrapper the LLM expands into the individual articles it contains.
The wrapper item is deleted and replaced with one `NewsItem` per extracted
article (deduplicated against existing items first), which are then
clustered and processed like anything else.

## Anthropic Batch API

When Anthropic is configured, bulk processing prefers Anthropic's
asynchronous Batch API over many synchronous calls — cheaper, and doesn't
compete with interactively-triggered processing for rate limits. An
`LLMBatch` row tracks each job's status
(`pending`/`cancelling`/`completed`/`cancelled`); polling runs one task per
pending batch so multiple jobs poll concurrently. A batch that exceeds
`LLM_BATCH_MAX_WAIT_MINUTES` is cancelled and any unprocessed items fall
back to synchronous processing automatically. Newsletter/email items
always go through the synchronous path, since they mutate the database
(splitting one item into several) rather than just annotating it.

## Embeddings

Regardless of which provider handles text generation, embeddings (used
for semantic clustering) always come from Ollama's `nomic-embed-text`
model (`OLLAMA_EMBEDDING_MODEL`, 768 dimensions). If Ollama is
unreachable, embedding generation fails gracefully and clustering falls
back to keyword-based matching — see {doc}`clustering`.

## Transparency

Every processed item and cluster records which provider and model
actually produced its summary (`llm_provider`/`llm_model`), shown via an
info icon in the feed — so it's never ambiguous whether a given summary
came from your local model or a cloud fallback.
