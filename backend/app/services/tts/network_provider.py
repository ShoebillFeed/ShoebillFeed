import os

import httpx

from app.services.tts.base import TTSProvider, VoiceInfo, SynthesisResult

# Conservative (Chatterbox-class slow-CPU) synthesis speed estimate, seconds
# per character of input text. Applied regardless of which engine the
# remote tts_service actually runs -- this provider has no visibility into
# that (see health_check()'s optimistic default for the same reason), and
# erring toward a generous timeout costs nothing (a fast engine's request
# just returns well before the deadline), whereas erring short reproduces
# the exact class of bug OllamaProvider's _timeout_for() fixed for the LLM
# side: a fixed timeout sized for the common case gets hit by a genuinely
# slow request instead of just taking longer to succeed.
_SECONDS_PER_CHAR_ESTIMATE = 0.85


def _timeout_for(text: str, floor: float) -> float:
    return max(floor, len(text) * _SECONDS_PER_CHAR_ESTIMATE)


class NetworkTTSProvider(TTSProvider):
    """Talks to a standalone tts_service/ container over HTTP instead of
    running an engine in-process -- the same shape as OllamaProvider talking
    to a standalone Ollama instance for LLM calls. Lets synthesis run on a
    different machine (e.g. one with a GPU) than the Celery worker itself."""

    provider_name = "network"

    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.default_timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        # Optimistic default (assume capable) until a real health check says
        # otherwise -- defaulting to False would misleadingly hide the speed
        # control for a healthy Piper/Kokoro deployment that just hasn't had
        # a health check run yet.
        self.supports_speech_rate = True
        # Pessimistic default here, unlike above: exaggeration is a genuinely
        # new control (not a pre-existing one that might be silently
        # inert), so hiding it until a health check confirms Chatterbox is
        # actually running is the safer failure mode.
        self.supports_exaggeration = False

    def list_voices(self, language: str) -> list[VoiceInfo]:
        resp = self.client.get(f"{self.base_url}/voices", params={"language": language})
        resp.raise_for_status()
        return [VoiceInfo(id=v["id"], language=v["language"], label=v["label"]) for v in resp.json()]

    def synthesize(
        self, text: str, voice_id: str, out_path: str, speech_rate: float = 1.0,
        exaggeration: float | None = None,
    ) -> SynthesisResult:
        resp = self.client.post(
            f"{self.base_url}/synthesize",
            json={"text": text, "voice_id": voice_id, "speech_rate": speech_rate, "exaggeration": exaggeration},
            timeout=_timeout_for(text, self.default_timeout),
        )
        resp.raise_for_status()

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(resp.content)

        # The service computes this during synthesis; trust it rather than
        # re-parsing the WAV we just wrote.
        duration = float(resp.headers.get("X-Duration-Seconds", 0.0))
        return SynthesisResult(audio_path=out_path, duration_seconds=duration)

    def health_check(self) -> bool:
        try:
            resp = self.client.get(f"{self.base_url}/health", timeout=5.0)
            if resp.status_code != 200:
                return False
            data = resp.json()
            if "supports_speech_rate" in data:
                self.supports_speech_rate = bool(data["supports_speech_rate"])
            if "supports_exaggeration" in data:
                self.supports_exaggeration = bool(data["supports_exaggeration"])
            return True
        except Exception:
            return False

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
