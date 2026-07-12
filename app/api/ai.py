from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.schemas.ai import PublicQuestionRequest, PublicQuestionResponse, VoiceQuestionRequest, VoiceQuestionResponse
from app.services.ai import public_question, public_voice_question

router = APIRouter(prefix="/api/ai")


@router.post("/public-question", response_model=PublicQuestionResponse)
async def ask(req: PublicQuestionRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    result = await public_question(req.roomId, req.question, req.needAudio)
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return PublicQuestionResponse(**result)


@router.post("/public-voice-question", response_model=VoiceQuestionResponse)
async def voice_ask(req: VoiceQuestionRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    result = await public_voice_question(
        req.roomId, user["userId"], req.channel, req.audioUrl,
        audio_format=req.audioFormat, text_hint=req.textHint,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return VoiceQuestionResponse(**result)
