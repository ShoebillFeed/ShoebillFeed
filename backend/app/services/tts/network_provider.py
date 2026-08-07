import os

import httpx

from app.services.tts.base import TTSProvider, VoiceInfo, SynthesisResult


class NetworkTTSProvider(TTSProvider):
    """Talks to a standalone tts_service/ container over HTTP instead of
    running an engine in-process -- the same shape as OllamaProvider talking
    to a standalone Ollama instance for LLM calls. Lets synthesis run on a
    different machine (e.g. one with a GPU) than the Celery worker itself."""

    provider_name = "network"

    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout)

    def list_voices(self, language: str) -> list[VoiceInfo]:
        resp = self.client.get(f"{self.base_url}/voices", params={"language": language})
        resp.raise_for_status()
        return [VoiceInfo(id=v["id"], language=v["language"], label=v["label"]) for v in resp.json()]

    def synthesize(self, text: str, voice_id: str, out_path: str, speech_rate: float = 1.0) -> SynthesisResult:
        resp = self.client.post(
            f"{self.base_url}/synthesize",
            json={"text": text, "voice_id": voice_id, "speech_rate": speech_rate},
        )
        resp.raise_for_status()

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(resp.content)

        # The service computes this during synthesis; trust it rather than
        # re-parsing the WAV we just wrote.
        duration = float(resp.headers.get("X-Duration-Seconds", 0.0))
        return SynthesisResult(audio_path=out_path, duration_seconds=duration)

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
