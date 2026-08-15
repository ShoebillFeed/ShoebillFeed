import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.engines.kokoro_engine import KokoroEngine


def _fake_result(samples):
    result = MagicMock()
    audio = MagicMock()
    audio.numpy.return_value = np.array(samples, dtype=np.float32)
    result.audio = audio
    return result


class TestKokoroEngineSynthesize:
    def test_concatenates_chunks_and_computes_duration(self):
        engine = KokoroEngine()
        fake_pipeline = MagicMock(return_value=[_fake_result([0.0] * 24000), _fake_result([0.0] * 12000)])
        with patch.object(engine, "_get_pipeline", return_value=fake_pipeline):
            wav_bytes, duration = engine.synthesize("Hello", "af_heart", speech_rate=1.0)

        assert duration == pytest.approx(1.5)  # 36000 samples / 24000 Hz
        assert len(wav_bytes) > 0

    def test_passes_voice_and_speed_through_to_the_pipeline(self):
        engine = KokoroEngine()
        fake_pipeline = MagicMock(return_value=[_fake_result([0.0] * 100)])
        with patch.object(engine, "_get_pipeline", return_value=fake_pipeline):
            engine.synthesize("Hi", "af_heart", speech_rate=1.3)

        fake_pipeline.assert_called_once_with("Hi", voice="af_heart", speed=1.3)

    def test_defaults_a_falsy_speech_rate_to_one(self):
        engine = KokoroEngine()
        fake_pipeline = MagicMock(return_value=[_fake_result([0.0] * 100)])
        with patch.object(engine, "_get_pipeline", return_value=fake_pipeline):
            engine.synthesize("Hi", "af_heart", speech_rate=0)

        fake_pipeline.assert_called_once_with("Hi", voice="af_heart", speed=1.0)

    def test_unknown_voice_raises_before_touching_a_pipeline(self):
        engine = KokoroEngine()
        with pytest.raises(ValueError, match="Unknown Kokoro voice"):
            engine.synthesize("Hi", "bogus_voice", speech_rate=1.0)

    def test_raises_if_the_pipeline_yields_no_audio(self):
        engine = KokoroEngine()
        result_without_audio = MagicMock()
        result_without_audio.audio = None
        fake_pipeline = MagicMock(return_value=[result_without_audio])
        with patch.object(engine, "_get_pipeline", return_value=fake_pipeline):
            with pytest.raises(ValueError, match="no audio"):
                engine.synthesize("Hi", "af_heart", speech_rate=1.0)


class TestKokoroEnginePipelineCaching:
    """Fakes the whole `kokoro` module via sys.modules so these don't need
    the real (heavy, torch-backed) package installed or a model download."""

    def test_reuses_a_pipeline_for_the_same_lang_code(self):
        engine = KokoroEngine()
        created = []

        class FakeKPipeline:
            def __init__(self, lang_code, device):
                created.append((lang_code, device))

        with patch.dict("sys.modules", {"kokoro": MagicMock(KPipeline=FakeKPipeline)}):
            engine._get_pipeline("a")
            engine._get_pipeline("a")

        assert len(created) == 1

    def test_use_cuda_selects_the_cuda_device(self):
        engine = KokoroEngine(use_cuda=True)
        created = []

        class FakeKPipeline:
            def __init__(self, lang_code, device):
                created.append((lang_code, device))

        with patch.dict("sys.modules", {"kokoro": MagicMock(KPipeline=FakeKPipeline)}):
            engine._get_pipeline("a")

        assert created == [("a", "cuda")]

    def test_default_device_is_cpu(self):
        engine = KokoroEngine(use_cuda=False)
        created = []

        class FakeKPipeline:
            def __init__(self, lang_code, device):
                created.append((lang_code, device))

        with patch.dict("sys.modules", {"kokoro": MagicMock(KPipeline=FakeKPipeline)}):
            engine._get_pipeline("e")

        assert created == [("e", "cpu")]

    def test_concurrent_first_requests_construct_the_pipeline_only_once(self):
        # FastAPI runs sync handlers in a thread pool -- without the lock in
        # _get_pipeline(), several concurrent first requests for the same
        # lang_code would each pass the "not yet cached" check and construct
        # a duplicate KPipeline.
        engine = KokoroEngine()
        created = []
        start_barrier = threading.Barrier(5)

        class FakeKPipeline:
            def __init__(self, lang_code, device):
                time.sleep(0.03)  # widen the window so concurrent callers can overlap
                created.append((lang_code, device))

        def call():
            start_barrier.wait()
            engine._get_pipeline("a")

        with patch.dict("sys.modules", {"kokoro": MagicMock(KPipeline=FakeKPipeline)}):
            threads = [threading.Thread(target=call) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert len(created) == 1
