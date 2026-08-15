"""Static catalog of Kokoro voices, grouped by Shoebill language code.

Voice names come from the hexgrad/Kokoro-82M model card
(https://huggingface.co/hexgrad/Kokoro-82M#voices-overview). Unlike Piper,
all of a language's voices live in one model repo -- only the ~80MB base
model plus each requested .pt voice pack (a few hundred KB) are ever
downloaded, lazily, on first use of that voice.

Only English ('a' = American) plus the espeak-backed languages (es/fr/it/pt)
are included: Kokoro's non-English G2P for those goes through
misaki.espeak.EspeakG2P, which is satisfied by the espeakng-loader package
already pulled in transitively via kokoro's own `misaki[en]` dependency --
no extra system packages or per-language misaki extras needed. Chinese and
Japanese are deliberately omitted for now: they need their own misaki[zh]/
misaki[ja] extras (jieba/pypinyin, fugashi/pyopenjtalk, ...), which would
meaningfully grow the image for two more languages. Add them the same way
if that tradeoff is worth it later.
"""

# Shoebill language code -> Kokoro's own lang_code (passed to KPipeline).
KOKORO_LANG_CODES: dict[str, str] = {
    "en": "a",  # American English. Kokoro also has 'b' (British); not
    # exposed separately since Shoebill only has one "en" language option.
    "es": "e",
    "fr": "f",
    "it": "i",
    "pt": "p",
}

# Shoebill language code -> Kokoro voice names for that language.
KOKORO_VOICES: dict[str, list[str]] = {
    "en": [
        "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica",
        "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
        "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam",
        "am_michael", "am_onyx", "am_puck", "am_santa",
    ],
    "es": ["ef_dora", "em_alex"],
    "fr": ["ff_siwis"],
    "it": ["if_sara", "im_nicola"],
    "pt": ["pf_dora", "pm_alex", "pm_santa"],
}


def language_for_voice(voice_id: str) -> str | None:
    """Shoebill language code that owns `voice_id`, or None if unknown."""
    for language, names in KOKORO_VOICES.items():
        if voice_id in names:
            return language
    return None
