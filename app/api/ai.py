from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.schemas.ai import PublicQuestionRequest, PublicQuestionResponse, VoiceQuestionRequest, VoiceQuestionResponse
from app.services.ai import public_question, public_voice_question
from app.services.messages import create_message
from app.services.realtime import room_connections

router = APIRouter(prefix="/api/ai")


async def _persist_public_exchange(
    room_id: str,
    user: dict,
    question: str,
    answer: str,
) -> None:
    question_message = create_message(
        room_id=room_id,
        user_id=user["userId"],
        user_name=user["userName"],
        content=question,
        message_type="user",
    )
    answer_message = create_message(
        room_id=room_id,
        user_id=None,
        user_name="AI Guide",
        content=answer,
        message_type="ai",
    )
    await room_connections.broadcast(room_id, {"type": "room.message", "data": question_message})
    await room_connections.broadcast(room_id, {"type": "room.message", "data": answer_message})


@router.post("/public-question", response_model=PublicQuestionResponse)
async def ask(req: PublicQuestionRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    room = require_room_member(req.roomId, user)
    enforce_rate_limit("ai", user["userId"], 30, 60)
    if room["status"] != "active":
        raise AppError(409, "ROOM_NOT_ACTIVE", "Public AI is available only in active rooms")
    result = await public_question(req.roomId, req.question, req.needAudio)
    if result is None:
        raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
    await _persist_public_exchange(req.roomId, user, req.question, result["answer"])
    return PublicQuestionResponse(**result)


@router.post("/public-voice-question", response_model=VoiceQuestionResponse)
async def voice_ask(req: VoiceQuestionRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    room = require_room_member(req.roomId, user)
    enforce_rate_limit("ai", user["userId"], 30, 60)
    if req.channel == "public" and room["status"] != "active":
        raise AppError(409, "ROOM_NOT_ACTIVE", "Public AI is available only in active rooms")
    result = await public_voice_question(
        req.roomId, user["userId"], req.channel, req.audioUrl,
        audio_format=req.audioFormat, text_hint=req.textHint,
    )
    if result is None:
        raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
    if req.channel == "public" and result.get("asrText") and result.get("answer"):
        await _persist_public_exchange(req.roomId, user, result["asrText"], result["answer"])
    return VoiceQuestionResponse(**result)
