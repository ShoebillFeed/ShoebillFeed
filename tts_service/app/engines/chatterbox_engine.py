import logging
import os
import threading

from app.engines.audio_utils import float_audio_to_wav_bytes
from app.engines.base import TTSEngine, VoiceInfo

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 24000  # Chatterbox's fixed S3Gen output rate.

# Shoebill language code -> Chatterbox's own SUPPORTED_LANGUAGES key
# (ChatterboxMultilingualTTS covers 23; these are the ones Shoebill also
# has). Missing from Chatterbox: Romanian, Ukrainian, Czech, Hungarian.
# Shoebill's one Norwegian variant ("nb") maps to Chatterbox's "no".
CHATTERBOX_LANGUAGES: dict[str, str] = {
    "en": "en", "de": "de", "fr": "fr", "es": "es", "it": "it", "nl": "nl",
    "pl": "pl", "pt": "pt", "ru": "ru", "zh": "zh", "ja": "ja", "ko": "ko",
    "tr": "tr", "sv": "sv", "da": "da", "fi": "fi", "nb": "no",
}

_VOICES_SUBDIR = "chatterbox_voices"
# .wav only -- librosa/soundfile reads it without extra system codecs (no
# ffmpeg needed in the image); keep operator-supplied reference clips in
# that format rather than widening this and hitting a missing-codec error
# at synthesis time.
_VOICE_EXTENSIONS = (".wav",)


class ChatterboxEngine(TTSEngine):
    """Unlike Piper/Kokoro's fixed named-voice catalogs, Chatterbox clones a
    voice from a short reference audio clip -- there's no bundled set of
    named voices to offer (and no way to source/license third-party voice
    recordings to ship here). Instead: a single "default" voice per language
    using the model checkpoint's own built-in speaker embedding (part of the
    model artifact itself, not something sourced separately), plus whatever
    reference clips an operator drops into
    `{TTS_MODEL_DIR}/chatterbox_voices/{language}/*.wav` -- scanned
    dynamically, so adding a cloned voice needs no code change.
    """

    engine_name = "chatterbox"
    supports_speech_rate = False

    def __init__(self, model_dir: str, use_cuda: bool = False):
        self.model_dir = model_dir
        self.use_cuda = use_cuda
        self._model = None
        self._default_conds = None
        # model.conds (voice conditioning) is mutable state on the model
        # instance, not a pure per-call argument the way Piper's syn_config
        # or Kokoro's voice= kwarg are -- generate(audio_prompt_path=...)
        # mutates it as a side effect. FastAPI runs sync handlers in a
        # thread pool, so two concurrent requests for different voices could
        # otherwise race (thread A's conditioning clobbered by thread B's
        # before A's generate() call reads it). Serialize the whole
        # set-conditioning-then-generate sequence per request instead of
        # trying to make the underlying model thread-safe.
        self._lock = threading.Lock()

    def list_voices(self, language: str) -> list[VoiceInfo]:
        if language not in CHATTERBOX_LANGUAGES:
            return []
        voices = [VoiceInfo(id=f"{language}:default", language=language, label="Default")]
        voices_dir = os.path.join(self.model_dir, _VOICES_SUBDIR, language)
        if os.path.isdir(voices_dir):
            for filename in sorted(os.listdir(voices_dir)):
                name, ext = os.path.splitext(filename)
                if ext.lower() in _VOICE_EXTENSIONS:
                    voices.append(VoiceInfo(id=f"{language}:{name}", language=language, label=name))
        return voices

    def synthesize(self, text: str, voice_id: str, speech_rate: float) -> tuple[bytes, float]:
        # speech_rate is intentionally ignored -- Chatterbox has no direct
        # speed control, unlike Piper's length_scale or Kokoro's speed.
        language, name = self._parse_voice_id(voice_id)
        chatterbox_lang = CHATTERBOX_LANGUAGES.get(language)
        if not chatterbox_lang:
            raise ValueError(f"Unsupported Chatterbox language for voice {voice_id!r}")

        audio_prompt_path = None
        if name != "default":
            audio_prompt_path = os.path.join(self.model_dir, _VOICES_SUBDIR, language, f"{name}.wav")
            if not os.path.exists(audio_prompt_path):
                raise ValueError(f"Unknown Chatterbox voice: {voice_id!r}")

        model = self._get_model()
        with self._lock:
            if audio_prompt_path is None:
                # Reset to the checkpoint's built-in voice -- a prior request
                # in this process may have left a cloned voice's conditioning
                # in place, and generate() only recomputes it when
                # audio_prompt_path is given.
                model.conds = self._default_conds
            wav_tensor = model.generate(
                text, language_id=chatterbox_lang, audio_prompt_path=audio_prompt_path,
            )
            audio = wav_tensor.squeeze(0).cpu().numpy()

        wav_bytes = float_audio_to_wav_bytes(audio, _SAMPLE_RATE)
        duration = len(audio) / _SAMPLE_RATE
        return wav_bytes, duration

    def _parse_voice_id(self, voice_id: str) -> tuple[str, str]:
        if ":" not in voice_id:
            raise ValueError(f"Unknown Chatterbox voice: {voice_id!r}")
        return tuple(voice_id.split(":", 1))

    def _get_model(self):
        if self._model is None:
            # Imported lazily: only needed if this engine is actually
            # selected (TTS_ENGINE=chatterbox), same reasoning as Kokoro.
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            device = "cuda" if self.use_cuda else "cpu"
            logger.info("Loading Chatterbox multilingual model on %s", device)
            self._model = ChatterboxMultilingualTTS.from_pretrained(device)
            self._default_conds = self._model.conds
        return self._model
