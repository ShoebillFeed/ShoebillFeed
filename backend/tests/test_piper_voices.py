import pytest

from app.services.tts.base import TTSProvider, VoiceInfo
from app.services.tts.piper_provider import PiperProvider
from app.services.tts.piper_voices import (
    PIPER_VOICE_CATALOG,
    curated_speaker_indices,
    model_name,
    model_relative_path,
)


def test_model_name_formats_lang_voice_quality():
    entry = {"lang": "en_US", "voice": "libritts_r", "quality": "medium", "speakers": 904}
    assert model_name(entry) == "en_US-libritts_r-medium"


def test_model_relative_path_uses_language_family_directory():
    entry = {"lang": "en_US", "voice": "libritts_r", "quality": "medium", "speakers": 904}
    assert model_relative_path(entry) == "en/en_US/libritts_r/medium/en_US-libritts_r-medium"


class TestCuratedSpeakerIndices:
    def test_single_speaker_returns_index_zero(self):
        assert curated_speaker_indices(1) == [0]

    def test_multi_speaker_returns_at_most_twelve_unique_sorted_indices(self):
        indices = curated_speaker_indices(904)
        assert len(indices) <= 12
        assert indices == sorted(set(indices))
        assert all(0 <= i < 904 for i in indices)

    def test_fewer_speakers_than_curated_count_returns_all_in_range(self):
        indices = curated_speaker_indices(3)
        assert all(0 <= i < 3 for i in indices)
        assert indices == sorted(set(indices))


class TestPiperProviderListVoices:
    def test_unknown_language_returns_empty_list(self, tmp_path):
        provider = PiperProvider(model_dir=str(tmp_path))
        assert provider.list_voices("xx") == []

    def test_single_speaker_language_returns_one_bare_voice_id(self, tmp_path):
        # fr is configured as a single-speaker model in the catalog.
        assert PIPER_VOICE_CATALOG["fr"]["speakers"] == 1
        provider = PiperProvider(model_dir=str(tmp_path))
        voices = provider.list_voices("fr")
        assert len(voices) == 1
        assert "#" not in voices[0].id
        assert voices[0].language == "fr"

    def test_multi_speaker_language_returns_indexed_voice_ids(self, tmp_path):
        # en is configured as a multi-speaker model (libritts_r) in the catalog.
        assert PIPER_VOICE_CATALOG["en"]["speakers"] > 1
        provider = PiperProvider(model_dir=str(tmp_path))
        voices = provider.list_voices("en")
        assert len(voices) == len(curated_speaker_indices(PIPER_VOICE_CATALOG["en"]["speakers"]))
        assert all("#" in v.id for v in voices)
        assert all(v.language == "en" for v in voices)
        assert len({v.id for v in voices}) == len(voices)  # all distinct


class _StubProvider(TTSProvider):
    """Minimal concrete TTSProvider so the base class's default
    pick_distinct_voices() can be exercised without touching Piper."""

    def __init__(self, voices):
        self._voices = voices

    def list_voices(self, language):
        return self._voices

    def synthesize(self, text, voice_id, out_path):
        raise NotImplementedError


class TestPickDistinctVoicesDefault:
    def test_returns_each_available_voice_once_when_enough_exist(self):
        provider = _StubProvider([VoiceInfo(id="a", language="en", label="A"), VoiceInfo(id="b", language="en", label="B")])
        assert provider.pick_distinct_voices("en", 2) == ["a", "b"]

    def test_cycles_through_voices_when_fewer_than_requested(self):
        provider = _StubProvider([VoiceInfo(id="a", language="en", label="A")])
        assert provider.pick_distinct_voices("en", 3) == ["a", "a", "a"]

    def test_raises_when_no_voices_available_for_language(self):
        provider = _StubProvider([])
        with pytest.raises(ValueError):
            provider.pick_distinct_voices("xx", 2)
