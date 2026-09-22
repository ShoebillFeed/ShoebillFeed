import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768  # nomic-embed-text; changing the model requires a schema migration

# Matches OllamaProvider.KEEP_ALIVE. Not imported from there on purpose --
# that module pulls in the whole LLM base for what is one string -- but the
# two must not drift. Without this, embeddings fall back to Ollama's own
# default (5 min), so the embedding model unloads between processing batches
# and pays a full reload on the next one; on a shared GPU that also means it
# keeps being re-admitted alongside the generate model instead of just
# staying resident.
_KEEP_ALIVE = "30m"


def generate_embedding(text: str) -> list[float] | None:
    """Generate a semantic embedding via Ollama.

    Returns None if Ollama is unreachable or the embedding model isn't pulled.
    Callers must handle None gracefully — clustering falls back to keyword Jaccard.
    """
    settings = get_settings()
    if not settings.ollama_base_url:
        return None

    try:
        resp = httpx.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": settings.ollama_embedding_model, "input": text,
                  "keep_alive": _KEEP_ALIVE},
            timeout=30.0,
        )
        if resp.status_code == 404:
            # Older Ollama versions use /api/embeddings with different schema
            resp = httpx.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": settings.ollama_embedding_model, "prompt": text,
                      "keep_alive": _KEEP_ALIVE},
                timeout=30.0,
            )
            resp.raise_for_status()
            vec = resp.json().get("embedding") or []
            if not vec:
                return None
            if len(vec) != EMBEDDING_DIM:
                logger.warning(
                    "Embedding dim mismatch: expected %d, got %d — "
                    "check OLLAMA_EMBEDDING_MODEL matches the schema's vector(768)",
                    EMBEDDING_DIM, len(vec),
                )
                return None
            return vec
        resp.raise_for_status()
        embeddings = resp.json().get("embeddings")
        if not embeddings or not embeddings[0]:
            return None
        vec = embeddings[0]
        if len(vec) != EMBEDDING_DIM:
            logger.warning(
                "Embedding dim mismatch: expected %d, got %d — "
                "check OLLAMA_EMBEDDING_MODEL matches the schema's vector(768)",
                EMBEDDING_DIM, len(vec),
            )
            return None
        return vec
    except Exception:
        logger.warning("Embedding generation failed", exc_info=True)
        return None
