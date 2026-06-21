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


def normalize_keyword(kw: str) -> str:
    """Normalize a keyword or keyphrase to its canonical form.

    Lowercases and lemmatizes each token so surface variants like
    'interest rates' and 'interest rate' map to the same key.
    """
    words = re.sub(r"[^\w\s]", " ", kw.lower().strip()).split()
    return " ".join(_lemmatize_word(w) for w in words if w)
