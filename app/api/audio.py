from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError

from app.schemas.audio import ASRRequest, ASRResponse, AudioUploadResponse, TTSRequest, TTSResponse
from app.services.audio import asr_transcribe, save_uploaded_audio, tts_synthesize
from app.services.rooms import record_voice_log

router = APIRouter(prefix="/api/audio")


def _validation_error(exc: ValidationError) -> HTTPException:
    return HTTPException(status_code=422, detail=exc.errors())


async def _asr_request_from_request(request: Request) -> ASRRequest:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        try:
            return ASRRequest.model_validate(await request.json())
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

    return ASRRequest(
        roomId=room_id,
        userId=user_id,
        channel=channel,
        audioUrl=saved["audioUrl"],
        audioFormat=saved["audioFormat"],
        textHint=str(form.get("textHint") or "") or None,
    )


@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio(
    roomId: str = Form(...),
    userId: str = Form(...),
    channel: str = Form("public"),
    audioFormat: str | None = Form(None),
    file: UploadFile = File(...),
):
    result = await save_uploaded_audio(roomId, userId, file, audioFormat)
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    record_voice_log(
        roomId,
        {
            "userId": userId,
            "channel": channel,
            "audioUrl": result["audioUrl"],
            "audioFormat": result["audioFormat"],
            "stage": "uploaded",
        },
    )
    return AudioUploadResponse(**result)


@router.post("/asr", response_model=ASRResponse)
async def asr(request: Request):
    req = await _asr_request_from_request(request)
    result = await asr_transcribe(
        req.roomId,
        req.userId,
        req.channel,
        req.audioUrl,
        audio_format=req.audioFormat,
        text_hint=req.textHint,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    record_voice_log(
        req.roomId,
        {
            "userId": req.userId,
            "channel": req.channel,
            "audioUrl": req.audioUrl,
            "audioFormat": req.audioFormat,
            "asrText": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
            "stage": "asr",
        },
    )
    return ASRResponse(
        text=result["text"],
        confidence=result["confidence"],
        provider=result.get("provider", ""),
        trace=result.get("trace", {}),
    )


@router.post("/tts", response_model=TTSResponse)
async def tts(req: TTSRequest):
    result = await tts_synthesize(req.text, req.voice, req.speed, req.audioFormat)
    return TTSResponse(
        audioUrl=result["audioUrl"],
        duration=result["duration"],
        provider=result.get("provider", ""),
        trace=result.get("trace", {}),
    )
