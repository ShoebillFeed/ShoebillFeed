import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.engines.factory import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shoebill TTS Service")


class VoiceOut(BaseModel):
    id: str
    language: str
    label: str


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice_id: str
    speech_rate: float = 1.0
    # Chatterbox-specific (emotion/delivery intensity); engines with no
    # equivalent ignore it. None = use the engine's own default.
    exaggeration: float | None = None


@app.get("/health")
def health():
    # get_engine() is cheap here -- it only constructs the engine object
    # (engine_name/supports_speech_rate are class attributes), never
    # triggers the actual model download/load, so this stays a fast
    # liveness check even for engines that lazily load a multi-GB model.
    engine = get_engine()
    return {
        "status": "ok",
        "engine": engine.engine_name,
        "supports_speech_rate": engine.supports_speech_rate,
        "supports_exaggeration": engine.supports_exaggeration,
    }


@app.get("/voices", response_model=list[VoiceOut])
def list_voices(language: str = Query(...)):
    engine = get_engine()
    voices = engine.list_voices(language)
    return [VoiceOut(id=v.id, language=v.language, label=v.label) for v in voices]


@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    engine = get_engine()
    try:
        wav_bytes, duration = engine.synthesize(req.text, req.voice_id, req.speech_rate, req.exaggeration)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Synthesis failed for voice_id=%r", req.voice_id)
        raise HTTPException(status_code=500, detail="Synthesis failed")

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"X-Duration-Seconds": str(duration)},
    )
