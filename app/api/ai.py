from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    PublicQuestionRequest,
    PublicQuestionResponse,
    VoiceQuestionRequest,
    VoiceQuestionResponse,
)
from app.services.ai import public_question, public_voice_question

router = APIRouter(prefix="/api/ai")


@router.post("/public-question", response_model=PublicQuestionResponse)
async def ask(req: PublicQuestionRequest):
    result = await public_question(req.roomId, req.question, req.needAudio)
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return PublicQuestionResponse(**result)


@router.post("/public-voice-question", response_model=VoiceQuestionResponse)
async def voice_ask(req: VoiceQuestionRequest):
    result = await public_voice_question(
        req.roomId,
        req.userId,
        req.channel,
        req.audioUrl,
        audio_format=req.audioFormat,
        text_hint=req.textHint,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return VoiceQuestionResponse(**result)
