import io
import wave

import numpy as np

from app.engines.audio_utils import float_audio_to_wav_bytes


class TestFloatAudioToWavBytes:
    def test_produces_a_valid_wav_with_expected_frame_count(self):
        audio = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        wav_bytes = float_audio_to_wav_bytes(audio, sample_rate=24000)

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            assert wav_file.getnchannels() == 1
            assert wav_file.getsampwidth() == 2
            assert wav_file.getframerate() == 24000
            assert wav_file.getnframes() == 5

    def test_clips_out_of_range_values_instead_of_overflowing(self):
        audio = np.array([2.0, -2.0], dtype=np.float32)
        wav_bytes = float_audio_to_wav_bytes(audio, sample_rate=24000)

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            frames = wav_file.readframes(2)
        samples = np.frombuffer(frames, dtype=np.int16)
        assert samples[0] == 32767
        assert samples[1] == -32767

    def test_different_sample_rates_are_honored(self):
        audio = np.zeros(100, dtype=np.float32)
        wav_bytes = float_audio_to_wav_bytes(audio, sample_rate=16000)

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            assert wav_file.getframerate() == 16000
