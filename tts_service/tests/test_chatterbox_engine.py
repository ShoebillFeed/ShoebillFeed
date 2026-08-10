from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.engines.chatterbox_engine import ChatterboxEngine


def _fake_wav_tensor(samples):
    tensor = MagicMock()
    tensor.squeeze.return_value.cpu.return_value.numpy.return_value = np.array(samples, dtype=np.float32)
    return tensor


class TestListVoices:
    def test_unsupported_language_returns_empty_list(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        assert engine.list_voices("xx") == []

    def test_supported_language_always_includes_default(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        voices = engine.list_voices("en")
        assert [v.id for v in voices] == ["en:default"]

    def test_scans_the_operator_supplied_reference_clips_directory(self, tmp_path):
        voices_dir = tmp_path / "chatterbox_voices" / "en"
        voices_dir.mkdir(parents=True)
        (voices_dir / "narrator.wav").write_bytes(b"fake wav")
        (voices_dir / "ignored.txt").write_bytes(b"not audio")

        engine = ChatterboxEngine(model_dir=str(tmp_path))
        voices = engine.list_voices("en")

        assert [v.id for v in voices] == ["en:default", "en:narrator"]

    def test_reference_clips_are_scoped_per_language(self, tmp_path):
        (tmp_path / "chatterbox_voices" / "de").mkdir(parents=True)
        (tmp_path / "chatterbox_voices" / "de" / "erzaehler.wav").write_bytes(b"fake wav")

        engine = ChatterboxEngine(model_dir=str(tmp_path))

        assert [v.id for v in engine.list_voices("en")] == ["en:default"]
        assert [v.id for v in engine.list_voices("de")] == ["de:default", "de:erzaehler"]


class TestParseVoiceId:
    def test_splits_language_and_name(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        assert engine._parse_voice_id("en:default") == ("en", "default")
        assert engine._parse_voice_id("de:narrator") == ("de", "narrator")

    def test_missing_colon_raises(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        with pytest.raises(ValueError, match="Unknown Chatterbox voice"):
            engine._parse_voice_id("bogus")


class TestSynthesize:
    def test_unsupported_language_raises(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        with pytest.raises(ValueError, match="Unsupported Chatterbox language"):
            engine.synthesize("Hi", "xx:default", speech_rate=1.0)

    def test_default_voice_does_not_pass_an_audio_prompt_and_resets_conds(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        fake_model = MagicMock()
        fake_model.generate.return_value = _fake_wav_tensor([0.0] * 24000)
        default_conds = object()
        engine._default_conds = default_conds
        fake_model.conds = "some other voice's conds"  # simulates a prior custom-voice request

        with patch.object(engine, "_get_model", return_value=fake_model):
            wav_bytes, duration = engine.synthesize("Hello", "en:default", speech_rate=1.0)

        fake_model.generate.assert_called_once_with("Hello", language_id="en", audio_prompt_path=None)
        assert fake_model.conds is default_conds  # reset before generate()
        assert duration == pytest.approx(1.0)
        assert len(wav_bytes) > 0

    def test_custom_voice_resolves_to_the_reference_clip_path(self, tmp_path):
        voices_dir = tmp_path / "chatterbox_voices" / "en"
        voices_dir.mkdir(parents=True)
        ref_path = voices_dir / "narrator.wav"
        ref_path.write_bytes(b"fake wav")

        engine = ChatterboxEngine(model_dir=str(tmp_path))
        fake_model = MagicMock()
        fake_model.generate.return_value = _fake_wav_tensor([0.0] * 100)

        with patch.object(engine, "_get_model", return_value=fake_model):
            engine.synthesize("Hi", "en:narrator", speech_rate=1.0)

        fake_model.generate.assert_called_once_with("Hi", language_id="en", audio_prompt_path=str(ref_path))

    def test_missing_reference_clip_raises(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        fake_model = MagicMock()
        with patch.object(engine, "_get_model", return_value=fake_model):
            with pytest.raises(ValueError, match="Unknown Chatterbox voice"):
                engine.synthesize("Hi", "en:nonexistent", speech_rate=1.0)
        fake_model.generate.assert_not_called()

    def test_speech_rate_is_ignored_without_error(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        fake_model = MagicMock()
        fake_model.generate.return_value = _fake_wav_tensor([0.0] * 100)
        with patch.object(engine, "_get_model", return_value=fake_model):
            engine.synthesize("Hi", "en:default", speech_rate=1.8)  # should not raise or affect the call
        fake_model.generate.assert_called_once_with("Hi", language_id="en", audio_prompt_path=None)


class TestGetModel:
    """Fakes the whole `chatterbox.mtl_tts` module via sys.modules so these
    don't need the real (very heavy, torch-backed) package installed."""

    def test_loads_once_and_caches(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path))
        created = []

        class FakeModel:
            def __init__(self):
                self.conds = "builtin-conds"

        class FakeChatterboxMultilingualTTS:
            @classmethod
            def from_pretrained(cls, device):
                created.append(device)
                return FakeModel()

        fake_module = MagicMock(ChatterboxMultilingualTTS=FakeChatterboxMultilingualTTS)
        with patch.dict("sys.modules", {"chatterbox": MagicMock(), "chatterbox.mtl_tts": fake_module}):
            model1 = engine._get_model()
            model2 = engine._get_model()

        assert model1 is model2
        assert len(created) == 1
        assert engine._default_conds == "builtin-conds"

    def test_use_cuda_selects_the_cuda_device(self, tmp_path):
        engine = ChatterboxEngine(model_dir=str(tmp_path), use_cuda=True)
        created = []

        class FakeModel:
            conds = None

        class FakeChatterboxMultilingualTTS:
            @classmethod
            def from_pretrained(cls, device):
                created.append(device)
                return FakeModel()

        fake_module = MagicMock(ChatterboxMultilingualTTS=FakeChatterboxMultilingualTTS)
        with patch.dict("sys.modules", {"chatterbox": MagicMock(), "chatterbox.mtl_tts": fake_module}):
            engine._get_model()

        assert created == ["cuda"]
