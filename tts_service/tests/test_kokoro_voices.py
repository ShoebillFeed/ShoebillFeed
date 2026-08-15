from app.engines.kokoro_voices import KOKORO_LANG_CODES, KOKORO_VOICES, language_for_voice


def test_every_catalog_language_has_a_lang_code():
    assert set(KOKORO_VOICES.keys()) == set(KOKORO_LANG_CODES.keys())


def test_every_catalog_language_has_at_least_one_voice():
    for language, voices in KOKORO_VOICES.items():
        assert len(voices) > 0, language


def test_voice_ids_are_unique_across_languages():
    all_ids = [v for voices in KOKORO_VOICES.values() for v in voices]
    assert len(all_ids) == len(set(all_ids))


class TestLanguageForVoice:
    def test_finds_the_owning_language(self):
        assert language_for_voice("ff_siwis") == "fr"

    def test_returns_none_for_an_unknown_voice(self):
        assert language_for_voice("bogus_voice") is None
