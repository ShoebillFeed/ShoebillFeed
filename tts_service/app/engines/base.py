from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VoiceInfo:
    id: str
    language: str
    label: str


class TTSEngine(ABC):
    """A synthesis backend. Mirrors Shoebill's own TTSProvider interface
    (backend/app/services/tts/base.py) one level down -- this is what a
    concrete engine (Piper, or whatever's added later) implements; the app
    talks to *this service* over HTTP, not to the engine directly."""

    engine_name: str = ""

    # Whether synthesize()'s `speech_rate` argument actually has any effect.
    # True is the common case; engines with no speed control at all (e.g.
    # Chatterbox) override this to False so /health can report it and the
    # app's Speech Speed slider can warn instead of silently doing nothing.
    supports_speech_rate: bool = True

    # Whether synthesize()'s `exaggeration` argument has any effect. False is
    # the common case (only Chatterbox's underlying library exposes an
    # emotion/delivery-intensity knob); lets /health report it so the
    # per-host exaggeration control only appears in the UI when it would
    # actually do something.
    supports_exaggeration: bool = False

    @abstractmethod
    def list_voices(self, language: str) -> list[VoiceInfo]:
        """Return all voices/speakers available for `language`. May be a
        single entry if only a single-speaker model is available."""
        ...

    @abstractmethod
    def synthesize(
        self, text: str, voice_id: str, speech_rate: float, exaggeration: float | None = None
    ) -> tuple[bytes, float]:
        """Render `text` to WAV audio using `voice_id`.

        `speech_rate` is listener-facing (1.0 = normal, > 1.0 = faster);
        engines with no speed control are free to ignore it.

        `exaggeration` is Chatterbox-specific (emotion/delivery intensity,
        None = use the engine's own default) -- engines with no equivalent
        are free to ignore it.

        Returns (wav_bytes, duration_seconds).
        """
        ...
