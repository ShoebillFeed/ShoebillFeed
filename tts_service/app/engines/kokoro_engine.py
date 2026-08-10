import logging
import threading

import numpy as np

from app.engines.audio_utils import float_audio_to_wav_bytes
from app.engines.base import TTSEngine, VoiceInfo
from app.engines.kokoro_voices import KOKORO_LANG_CODES, KOKORO_VOICES, language_for_voice

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 24000  # Kokoro's fixed output rate, not configurable per-voice.


class KokoroEngine(TTSEngine):
    engine_name = "kokoro"

    def __init__(self, use_cuda: bool = False):
        self.use_cuda = use_cuda
        # One KPipeline per Kokoro lang_code, lazily constructed and cached --
        # each owns its own G2P + loaded voice packs, so reuse matters.
        self._pipelines: dict[str, object] = {}
        # See PiperEngine._load_lock for why this exists: FastAPI's sync
        # handlers run in a thread pool, so two concurrent first-requests for
        # the same lang_code could otherwise both construct a KPipeline.
        self._pipeline_lock = threading.Lock()

    def list_voices(self, language: str) -> list[VoiceInfo]:
        names = KOKORO_VOICES.get(language, [])
        return [VoiceInfo(id=name, language=language, label=name) for name in names]

    def synthesize(self, text: str, voice_id: str, speech_rate: float) -> tuple[bytes, float]:
        language = language_for_voice(voice_id)
        if language is None:
            raise ValueError(f"Unknown Kokoro voice: {voice_id!r}")
        pipeline = self._get_pipeline(KOKORO_LANG_CODES[language])

        chunks = [
            result.audio.numpy()
            for result in pipeline(text, voice=voice_id, speed=speech_rate or 1.0)
            if result.audio is not None
        ]
        if not chunks:
            raise ValueError(f"Kokoro produced no audio for voice {voice_id!r}")
        audio = np.concatenate(chunks)

        wav_bytes = float_audio_to_wav_bytes(audio, _SAMPLE_RATE)
        duration = len(audio) / _SAMPLE_RATE
        return wav_bytes, duration

    def _get_pipeline(self, lang_code: str):
        pipeline = self._pipelines.get(lang_code)
        if pipeline is not None:
            return pipeline

        with self._pipeline_lock:
            pipeline = self._pipelines.get(lang_code)
            if pipeline is not None:
                return pipeline

            # Imported lazily: torch + kokoro are only needed if this engine
            # is actually selected (TTS_ENGINE=kokoro), so a piper-only
            # deployment never pays the import cost even though both
            # engines' dependencies are installed in the same image.
            from kokoro import KPipeline

            device = "cuda" if self.use_cuda else "cpu"
            logger.info("Loading Kokoro pipeline for lang_code=%r on %s", lang_code, device)
            pipeline = KPipeline(lang_code=lang_code, device=device)
            self._pipelines[lang_code] = pipeline
            return pipeline
