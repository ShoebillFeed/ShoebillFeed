import io
import logging
import os
import wave

import httpx
from piper import PiperVoice
from piper.config import SynthesisConfig

from app.engines.base import TTSEngine, VoiceInfo
from app.engines.piper_voices import (
    PIPER_VOICE_CATALOG,
    HF_VOICES_BASE_URL,
    model_name,
    model_relative_path,
    curated_speaker_indices,
)

logger = logging.getLogger(__name__)


class PiperEngine(TTSEngine):
    engine_name = "piper"

    def __init__(self, model_dir: str, use_cuda: bool = False):
        self.model_dir = model_dir
        self.use_cuda = use_cuda
        os.makedirs(self.model_dir, exist_ok=True)
        self._loaded_voices: dict[str, PiperVoice] = {}

    def list_voices(self, language: str) -> list[VoiceInfo]:
        entry = PIPER_VOICE_CATALOG.get(language)
        if not entry:
            return []
        name = model_name(entry)
        speakers = entry["speakers"]
        if speakers <= 1:
            return [VoiceInfo(id=name, language=language, label=name)]
        return [
            VoiceInfo(id=f"{name}#{i}", language=language, label=f"Speaker {i} ({name})")
            for i in curated_speaker_indices(speakers)
        ]

    def synthesize(self, text: str, voice_id: str, speech_rate: float) -> tuple[bytes, float]:
        model, speaker_id = self._parse_voice_id(voice_id)
        voice = self._load_voice(model)
        # Piper's length_scale is phoneme-duration scaling, inverted from our
        # listener-facing "speed" (< 1 = faster speech, so invert here). 1.0
        # is Piper's own default too, so a normal-speed show is a no-op.
        length_scale = 1.0 / speech_rate if speech_rate else 1.0
        syn_config = SynthesisConfig(speaker_id=speaker_id, length_scale=length_scale)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)
        wav_bytes = buf.getvalue()

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate) if rate else 0.0

        return wav_bytes, duration

    def _parse_voice_id(self, voice_id: str) -> tuple[str, int | None]:
        if "#" in voice_id:
            model, speaker = voice_id.split("#", 1)
            return model, int(speaker)
        return voice_id, None

    def _load_voice(self, model: str) -> PiperVoice:
        if model in self._loaded_voices:
            return self._loaded_voices[model]

        onnx_path, config_path = self._ensure_model_downloaded(model)
        voice = PiperVoice.load(onnx_path, config_path=config_path, use_cuda=self.use_cuda)
        self._loaded_voices[model] = voice
        return voice

    def _ensure_model_downloaded(self, model: str) -> tuple[str, str]:
        entry = next((e for e in PIPER_VOICE_CATALOG.values() if model_name(e) == model), None)
        if not entry:
            raise ValueError(f"Unknown Piper voice model: {model!r}")

        onnx_path = os.path.join(self.model_dir, f"{model}.onnx")
        config_path = os.path.join(self.model_dir, f"{model}.onnx.json")
        rel_path = model_relative_path(entry)

        if not os.path.exists(onnx_path):
            logger.info("Downloading Piper voice model %s", model)
            self._download(f"{HF_VOICES_BASE_URL}/{rel_path}.onnx", onnx_path)
        if not os.path.exists(config_path):
            self._download(f"{HF_VOICES_BASE_URL}/{rel_path}.onnx.json", config_path)

        return onnx_path, config_path

    def _download(self, url: str, dest_path: str) -> None:
        tmp_path = f"{dest_path}.part"
        with httpx.stream("GET", url, follow_redirects=True, timeout=300) as response:
            response.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        os.replace(tmp_path, dest_path)
