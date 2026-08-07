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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/voices", response_model=list[VoiceOut])
def list_voices(language: str = Query(...)):
    engine = get_engine()
    voices = engine.list_voices(language)
    return [VoiceOut(id=v.id, language=v.language, label=v.label) for v in voices]


@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    engine = get_engine()
    try:
        wav_bytes, duration = engine.synthesize(req.text, req.voice_id, req.speech_rate)
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
