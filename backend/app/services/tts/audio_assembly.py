import os
import subprocess
import tempfile
import wave
from dataclasses import dataclass

_SILENCE_GAP_SECONDS = 0.4
_SAMPLE_RATE = 22050  # matches Piper's default output rate for medium-quality models


@dataclass
class AssembleResult:
    path: str
    duration_seconds: float


def _write_silence_wav(path: str, seconds: float, rate: int = _SAMPLE_RATE) -> None:
    n_frames = int(seconds * rate)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(b"\x00\x00" * n_frames)


def assemble_episode(turn_wav_paths: list[str], turn_durations: list[float], out_path: str) -> AssembleResult:
    """Concatenates per-turn WAV files (with a short silence gap between turns)
    and encodes the result to a single MP3 file at `out_path` via ffmpeg."""
    if not turn_wav_paths:
        raise ValueError("No audio turns to assemble")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        silence_path = os.path.join(tmp_dir, "silence.wav")
        _write_silence_wav(silence_path, _SILENCE_GAP_SECONDS)

        concat_list_path = os.path.join(tmp_dir, "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for i, wav_path in enumerate(turn_wav_paths):
                if i > 0:
                    f.write(f"file '{silence_path}'\n")
                f.write(f"file '{wav_path}'\n")

        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
                "-codec:a", "libmp3lame", "-b:a", "96k", "-ar", "44100", "-ac", "1",
                out_path,
            ],
            check=True,
            capture_output=True,
        )

    total_seconds = sum(turn_durations) + _SILENCE_GAP_SECONDS * max(0, len(turn_wav_paths) - 1)
    return AssembleResult(path=out_path, duration_seconds=total_seconds)
