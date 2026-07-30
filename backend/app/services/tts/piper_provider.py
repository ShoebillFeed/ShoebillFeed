import logging
import os
import wave

import httpx

from app.services.tts.base import TTSProvider, VoiceInfo, SynthesisResult
from app.services.tts.piper_voices import (
    PIPER_VOICE_CATALOG,
    HF_VOICES_BASE_URL,
    model_name,
    model_relative_path,
    curated_speaker_indices,
)

logger = logging.getLogger(__name__)


class PiperProvider(TTSProvider):
    provider_name = "piper"

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self._loaded_voices: dict[str, object] = {}  # model_name -> piper.PiperVoice

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

    def synthesize(self, text: str, voice_id: str, out_path: str) -> SynthesisResult:
        from piper.config import SynthesisConfig  # imported lazily alongside PiperVoice

        model, speaker_id = self._parse_voice_id(voice_id)
        voice = self._load_voice(model)
        syn_config = SynthesisConfig(speaker_id=speaker_id) if speaker_id is not None else None

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with wave.open(out_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        with wave.open(out_path, "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate) if rate else 0.0

        return SynthesisResult(audio_path=out_path, duration_seconds=duration)

    def _parse_voice_id(self, voice_id: str) -> tuple[str, int | None]:
        if "#" in voice_id:
            model, speaker = voice_id.split("#", 1)
            return model, int(speaker)
        return voice_id, None

    def _load_voice(self, model: str):
        if model in self._loaded_voices:
            return self._loaded_voices[model]

        from piper import PiperVoice  # imported lazily: heavy, only needed on the podcast worker

        onnx_path, config_path = self._ensure_model_downloaded(model)
        voice = PiperVoice.load(onnx_path, config_path=config_path)
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
