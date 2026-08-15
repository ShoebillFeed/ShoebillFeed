"""Static catalog mapping Shoebill's language codes to Piper voice models.

Kept in sync by hand with backend/app/services/tts/piper_voices.py -- this
service is an independently built/deployed project (like frontend/ and
backend/ are from each other), so it doesn't share code across that
boundary. If you add a language here, add it there too (and vice versa),
since the language codes must match what Shoebill's UI offers.

Model files are hosted on Hugging Face at
https://huggingface.co/rhasspy/piper-voices under
`{family}/{lang}/{voice_name}/{quality}/{lang}-{voice_name}-{quality}.onnx`
(plus a sibling `.onnx.json` config file). See
https://github.com/rhasspy/piper/blob/master/VOICES.md for the full catalog.
Voice model files carry their own individual licenses (commonly CC-BY-SA),
separate from the piper-tts library's own license.

Languages with no known Piper voice (e.g. Japanese, Korean) are intentionally
omitted -- list_voices() returns an empty list for them rather than
silently substituting a wrong-language voice.
"""

HF_VOICES_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# language code (as used by UserSettings.output_language / PodcastShow.language)
# -> {"lang": IANA-ish Piper language dir, "voice": voice name, "quality": ...,
#     "speakers": speaker count (1 = single-speaker model)}
PIPER_VOICE_CATALOG: dict[str, dict] = {
    "en": {"lang": "en_US", "voice": "libritts_r", "quality": "medium", "speakers": 904},
    "de": {"lang": "de_DE", "voice": "mls", "quality": "medium", "speakers": 236},
    "fr": {"lang": "fr_FR", "voice": "siwis", "quality": "medium", "speakers": 1},
    "es": {"lang": "es_ES", "voice": "davefx", "quality": "medium", "speakers": 1},
    "it": {"lang": "it_IT", "voice": "paola", "quality": "medium", "speakers": 1},
    "pt": {"lang": "pt_BR", "voice": "faber", "quality": "medium", "speakers": 1},
    "nl": {"lang": "nl_NL", "voice": "mls", "quality": "medium", "speakers": 1},
    "pl": {"lang": "pl_PL", "voice": "darkman", "quality": "medium", "speakers": 1},
    "ru": {"lang": "ru_RU", "voice": "irina", "quality": "medium", "speakers": 1},
    "uk": {"lang": "uk_UA", "voice": "ukrainian_tts", "quality": "medium", "speakers": 1},
    "zh": {"lang": "zh_CN", "voice": "huayan", "quality": "medium", "speakers": 1},
    "tr": {"lang": "tr_TR", "voice": "fahrettin", "quality": "medium", "speakers": 1},
    "cs": {"lang": "cs_CZ", "voice": "jirka", "quality": "medium", "speakers": 1},
    "da": {"lang": "da_DK", "voice": "talesyntese", "quality": "medium", "speakers": 1},
    "fi": {"lang": "fi_FI", "voice": "harri", "quality": "medium", "speakers": 1},
    "hu": {"lang": "hu_HU", "voice": "anna", "quality": "medium", "speakers": 1},
    "nb": {"lang": "no_NO", "voice": "talesyntese", "quality": "medium", "speakers": 1},
    "ro": {"lang": "ro_RO", "voice": "mihai", "quality": "medium", "speakers": 1},
    "sv": {"lang": "sv_SE", "voice": "nst", "quality": "medium", "speakers": 1},
}

# How many distinct speaker indices to surface in the voice picker for a
# multi-speaker model (evenly sampled across the full range — we have no
# per-speaker metadata to pick "the most distinct-sounding" ones).
_CURATED_SPEAKER_COUNT = 12


def model_name(entry: dict) -> str:
    return f"{entry['lang']}-{entry['voice']}-{entry['quality']}"


def model_relative_path(entry: dict) -> str:
    family = entry["lang"].split("_")[0]
    name = model_name(entry)
    return f"{family}/{entry['lang']}/{entry['voice']}/{entry['quality']}/{name}"


def curated_speaker_indices(speaker_count: int) -> list[int]:
    if speaker_count <= 1:
        return [0]
    n = min(_CURATED_SPEAKER_COUNT, speaker_count)
    step = speaker_count / n
    return sorted({int(i * step) for i in range(n)})
