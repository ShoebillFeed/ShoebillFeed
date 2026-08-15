# Short, simple sentences for the "preview this voice" feature (podcast show
# form) -- deliberately not routed through the LLM (this is a fixed sample,
# not content that needs generating) and deliberately per-language rather
# than always English: feeding English text to a non-English voice model
# would mispronounce it through the wrong phoneme set, defeating the point
# of a preview. Keys mirror PIPER_VOICE_CATALOG in piper_voices.py, the
# broadest of the three engines' language coverage.
PREVIEW_PHRASES: dict[str, str] = {
    "en": "Hello, this is a preview of this voice.",
    "de": "Hallo, das ist eine Vorschau dieser Stimme.",
    "fr": "Bonjour, ceci est un aperçu de cette voix.",
    "es": "Hola, esta es una vista previa de esta voz.",
    "it": "Ciao, questa è un'anteprima di questa voce.",
    "pt": "Olá, esta é uma prévia desta voz.",
    "nl": "Hallo, dit is een voorbeeld van deze stem.",
    "pl": "Cześć, to jest podgląd tego głosu.",
    "ru": "Привет, это предварительное прослушивание этого голоса.",
    "uk": "Привіт, це попереднє прослуховування цього голосу.",
    "zh": "你好，这是这个声音的预览。",
    "tr": "Merhaba, bu bir ses önizlemesidir.",
    "cs": "Ahoj, toto je ukázka tohoto hlasu.",
    "da": "Hej, dette er en forhåndsvisning af denne stemme.",
    "fi": "Hei, tämä on esikatselu tästä äänestä.",
    "hu": "Szia, ez egy előnézet ebből a hangból.",
    "nb": "Hei, dette er en forhåndsvisning av denne stemmen.",
    "ro": "Salut, aceasta este o previzualizare a acestei voci.",
    "sv": "Hej, det här är en förhandsvisning av den här rösten.",
}


def preview_phrase_for(language: str) -> str:
    return PREVIEW_PHRASES.get(language, PREVIEW_PHRASES["en"])
