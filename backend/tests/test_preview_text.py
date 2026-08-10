from app.services.tts.preview_text import PREVIEW_PHRASES, preview_phrase_for


def test_returns_the_phrase_for_a_known_language():
    assert preview_phrase_for("de") == PREVIEW_PHRASES["de"]


def test_falls_back_to_english_for_an_unknown_language():
    assert preview_phrase_for("xx") == PREVIEW_PHRASES["en"]


def test_every_phrase_is_non_empty():
    assert all(phrase.strip() for phrase in PREVIEW_PHRASES.values())
