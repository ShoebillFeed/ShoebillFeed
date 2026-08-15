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

    # Whether synthesize()'s `speech_rate` argument actually has any effect
    # for this provider. True is the common case (Piper, Kokoro); Chatterbox
    # has no speed control in the underlying library at all and silently
    # ignores it, so the frontend needs to know this to warn users instead
    # of letting the Speech Speed slider look functional and do nothing.
    supports_speech_rate: bool = True

    # Whether synthesize()'s `exaggeration` argument has any effect. False is
    # the common case -- only Chatterbox's underlying library exposes an
    # emotion/delivery-intensity knob -- so the podcast show form only shows
    # the per-host exaggeration control when this is True.
    supports_exaggeration: bool = False

    @abstractmethod
    def list_voices(self, language: str) -> list[VoiceInfo]:
        """Return all voices/speakers available for `language`. May be a single
        entry if only a single-speaker model is available for that language."""
        ...

    @abstractmethod
    def synthesize(
        self, text: str, voice_id: str, out_path: str, speech_rate: float = 1.0,
        exaggeration: float | None = None,
    ) -> SynthesisResult:
        """Render `text` to a WAV file at `out_path` using `voice_id`.

        `speech_rate` is listener-facing (1.0 = normal, > 1.0 = faster);
        providers with no speed control are free to ignore it.

        `exaggeration` is Chatterbox-specific (emotion/delivery intensity,
        None = use the engine's own default); providers with no equivalent
        are free to ignore it.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Cheap reachability check -- True if this provider is ready to
        synthesize right now. Only ever called on-demand from Settings (not
        on a hot path, and not wired into the app's own docker-compose
        healthcheck, since TTS_PROVIDER=network reaching an unresponsive
        remote host could make that check slow/flaky), so a short blocking
        call here is fine. Implementations should catch their own errors and
        return False rather than raise.
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
