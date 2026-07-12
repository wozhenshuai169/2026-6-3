from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.schemas.audio import ASRRequest, ASRResponse, TTSRequest, TTSResponse
from app.services.audio import asr_transcribe, tts_synthesize

router = APIRouter(prefix="/api/audio")


@router.post("/asr", response_model=ASRResponse)
async def asr(req: ASRRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    result = await asr_transcribe(
        req.roomId, user["userId"], req.channel, req.audioUrl,
        audio_format=req.audioFormat, text_hint=req.textHint,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return ASRResponse(text=result["text"], confidence=result["confidence"])


@router.post("/tts", response_model=TTSResponse)
async def tts(req: TTSRequest, user: dict = Depends(get_current_user)):
    result = await tts_synthesize(req.text, req.voice, req.speed, req.audioFormat)
    return TTSResponse(audioUrl=result["audioUrl"], duration=result["duration"])
