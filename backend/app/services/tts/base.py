from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VoiceInfo:
    id: str
    language: str
    label: str


@dataclass
class SynthesisResult:
    audio_path: str
    duration_seconds: float


class TTSProvider(ABC):
    provider_name: str = ""

    @abstractmethod
    def list_voices(self, language: str) -> list[VoiceInfo]:
        """Return all voices/speakers available for `language`. May be a single
        entry if only a single-speaker model is available for that language."""
        ...

    @abstractmethod
    def synthesize(self, text: str, voice_id: str, out_path: str, speech_rate: float = 1.0) -> SynthesisResult:
        """Render `text` to a WAV file at `out_path` using `voice_id`.

        `speech_rate` is listener-facing (1.0 = normal, > 1.0 = faster);
        providers with no speed control are free to ignore it.
        """
        ...

    def pick_distinct_voices(self, language: str, count: int) -> list[str]:
        """Up to `count` distinct voice ids for `language`; if fewer are available,
        cycles/reuses them so every host still gets a voice assigned (graceful
        degradation for languages with only one available voice)."""
        voices = self.list_voices(language)
        if not voices:
            raise ValueError(f"No TTS voices available for language {language!r}")
        ids = [v.id for v in voices]
        return [ids[i % len(ids)] for i in range(count)]
