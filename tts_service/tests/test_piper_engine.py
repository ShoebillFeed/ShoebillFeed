from app.engines.piper_voices import (
    PIPER_VOICE_CATALOG,
    curated_speaker_indices,
    model_name,
    model_relative_path,
)
from app.engines.piper_engine import PiperEngine


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


class TestPiperEngineListVoices:
    def test_unknown_language_returns_empty_list(self, tmp_path):
        engine = PiperEngine(model_dir=str(tmp_path))
        assert engine.list_voices("xx") == []

    def test_single_speaker_language_returns_one_bare_voice_id(self, tmp_path):
        assert PIPER_VOICE_CATALOG["fr"]["speakers"] == 1
        engine = PiperEngine(model_dir=str(tmp_path))
        voices = engine.list_voices("fr")
        assert len(voices) == 1
        assert "#" not in voices[0].id
        assert voices[0].language == "fr"

    def test_multi_speaker_language_returns_indexed_voice_ids(self, tmp_path):
        assert PIPER_VOICE_CATALOG["en"]["speakers"] > 1
        engine = PiperEngine(model_dir=str(tmp_path))
        voices = engine.list_voices("en")
        assert all("#" in v.id for v in voices)
        assert len({v.id for v in voices}) == len(voices)  # all distinct


class TestParseVoiceId:
    def test_splits_model_and_speaker_index(self, tmp_path):
        engine = PiperEngine(model_dir=str(tmp_path))
        model, speaker = engine._parse_voice_id("en_US-libritts_r-medium#42")
        assert model == "en_US-libritts_r-medium"
        assert speaker == 42

    def test_single_speaker_voice_id_has_no_speaker_index(self, tmp_path):
        engine = PiperEngine(model_dir=str(tmp_path))
        model, speaker = engine._parse_voice_id("fr_FR-siwis-medium")
        assert model == "fr_FR-siwis-medium"
        assert speaker is None


class TestPiperEngineConstruction:
    def test_creates_model_dir_if_missing(self, tmp_path):
        model_dir = tmp_path / "voices"
        assert not model_dir.exists()
        PiperEngine(model_dir=str(model_dir))
        assert model_dir.exists()

    def test_use_cuda_defaults_to_false(self, tmp_path):
        engine = PiperEngine(model_dir=str(tmp_path))
        assert engine.use_cuda is False

    def test_use_cuda_can_be_enabled(self, tmp_path):
        engine = PiperEngine(model_dir=str(tmp_path), use_cuda=True)
        assert engine.use_cuda is True
