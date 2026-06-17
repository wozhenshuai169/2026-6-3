from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from app.schemas.ai import (
    PublicQuestionRequest,
    PublicQuestionResponse,
    VoiceQuestionRequest,
    VoiceQuestionResponse,
)
from app.services.ai import public_question, public_voice_question
from app.services.audio import save_uploaded_audio

router = APIRouter(prefix="/api/ai")


def _validation_error(exc: ValidationError) -> HTTPException:
    return HTTPException(status_code=422, detail=exc.errors())


async def _voice_request_from_request(request: Request) -> VoiceQuestionRequest:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        try:
            return VoiceQuestionRequest.model_validate(await request.json())
        except ValidationError as exc:
            raise _validation_error(exc) from exc

    form = await request.form()
    file = form.get("file")
    room_id = str(form.get("roomId") or "")
    user_id = str(form.get("userId") or "")
    channel = str(form.get("channel") or "public")
    if not room_id or not user_id or file is None or not hasattr(file, "read"):
        raise HTTPException(status_code=422, detail="roomId, userId and file are required")

    saved = await save_uploaded_audio(
        room_id,
        user_id,
        file,
        audio_format=str(form.get("audioFormat") or "") or None,
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return VoiceQuestionRequest(
        roomId=room_id,
        userId=user_id,
        channel=channel,
        audioUrl=saved["audioUrl"],
        audioFormat=saved["audioFormat"],
        textHint=str(form.get("textHint") or "") or None,
    )


@router.post("/public-question", response_model=PublicQuestionResponse)
async def ask(req: PublicQuestionRequest):
    result = await public_question(req.roomId, req.question, req.needAudio)
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return PublicQuestionResponse(**result)


@router.post("/public-voice-question", response_model=VoiceQuestionResponse)
async def voice_ask(request: Request):
    req = await _voice_request_from_request(request)
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
