import re
import logging

logger = logging.getLogger(__name__)

try:
    from nltk.stem import WordNetLemmatizer
    _lemmatizer = WordNetLemmatizer()
    _lemmatizer.lemmatize("test")  # triggers lazy corpus load; raises if corpus missing
    _USE_NLTK = True
except Exception:
    logger.warning("NLTK WordNet corpus unavailable — keyword normalization disabled")
    _USE_NLTK = False


def _lemmatize_word(word: str) -> str:
    if not _USE_NLTK:
        return word
    # Noun lemmatization first: handles plurals ("rates" → "rate")
    noun = _lemmatizer.lemmatize(word, pos="n")
    if noun != word:
        return noun
    # Verb lemmatization fallback: handles gerunds/past tense ("hiking" → "hike")
    return _lemmatizer.lemmatize(word, pos="v")


def merge_keywords(primary: list[str] | None, extra: list[str] | None) -> list[str] | None:
    """Combine two keyword lists, `primary` first, dropping case-insensitive
    duplicates. Returns None for an empty result so the column stays NULL
    rather than holding an empty array.

    Used to fold source-supplied keywords (NewsItem.source_keywords) into the
    LLM's own output at processing time. Compared case-insensitively rather
    than via normalize_keyword(): this guards the stored, human-readable list
    against visible near-duplicates, while normalization is what the
    clustering and weight code applies when it needs canonical forms.
    """
    merged: list[str] = []
    seen: set[str] = set()
    for kw in list(primary or []) + list(extra or []):
        cleaned = (kw or "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(cleaned)
    return merged or None


def normalize_keyword(kw: str) -> str:
    """Normalize a keyword or keyphrase to its canonical form.

    Lowercases and lemmatizes each token so surface variants like
    'interest rates' and 'interest rate' map to the same key.
    """
    words = re.sub(r"[^\w\s]", " ", kw.lower().strip()).split()
    return " ".join(_lemmatize_word(w) for w in words if w)
