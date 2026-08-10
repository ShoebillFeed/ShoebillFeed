import io
import wave

import numpy as np


def float_audio_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Mono float32 samples in [-1, 1] -> 16-bit PCM WAV bytes. Shared by
    engines (Kokoro, Chatterbox) whose models hand back raw float audio
    arrays rather than writing a WAV file themselves the way Piper does."""
    pcm16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm16.tobytes())
    return buf.getvalue()
