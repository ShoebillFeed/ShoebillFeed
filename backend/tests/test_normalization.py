from app.services.normalization import normalize_keyword


def test_lowercases():
    assert normalize_keyword("Interest") == "interest"


def test_lemmatizes_plural_nouns():
    # "rates" -> "rate" so surface variants collapse to the same key
    assert normalize_keyword("rates") == normalize_keyword("rate")


def test_lemmatizes_gerunds():
    assert normalize_keyword("hiking") == normalize_keyword("hike")


def test_strips_trailing_punctuation():
    assert normalize_keyword("AI,") == normalize_keyword("AI")


def test_internal_punctuation_becomes_a_word_boundary():
    # "A.I." isn't collapsed to "ai" -- the dots split it into two tokens,
    # same as any other non-word separator would.
    assert normalize_keyword("A.I.") == "a i"


def test_collapses_surface_variants_of_a_keyphrase():
    assert normalize_keyword("interest rates") == normalize_keyword("interest rate")


def test_empty_string():
    assert normalize_keyword("") == ""

def test_whitespace_only():
    assert normalize_keyword("   ") == ""
