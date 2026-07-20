from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.core.config import settings
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.schemas.audio import ASRRequest, ASRResponse, AudioUploadResponse, TTSRequest, TTSResponse
from app.services.audio import asr_transcribe, tts_synthesize

router = APIRouter(prefix="/api/audio")

UPLOAD_DIR = Path("uploads") / "audio"
_AUDIO_MIME = {
    ".wav": {"audio/wav", "audio/x-wav"},
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".webm": {"audio/webm", "video/webm"},
    ".ogg": {"audio/ogg", "application/ogg"},
    ".m4a": {"audio/mp4", "audio/x-m4a"},
}


def _valid_audio_signature(suffix: str, header: bytes) -> bool:
    return {
        ".wav": header.startswith(b"RIFF") and header[8:12] == b"WAVE",
        ".mp3": header.startswith(b"ID3") or header[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"},
        ".webm": header.startswith(b"\x1aE\xdf\xa3"),
        ".ogg": header.startswith(b"OggS"),
        ".m4a": b"ftyp" in header[:16],
    }.get(suffix, False)


@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    roomId: str = Form(...),
    userId: str = Form(...),
    channel: str = Form("public"),
    user: dict = Depends(get_current_user),
):
    del channel
    require_matching_user(userId, user)
    require_room_member(roomId, user)
    enforce_rate_limit("upload", user["userId"], 10, 600)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _AUDIO_MIME or file.content_type not in _AUDIO_MIME[suffix]:
        raise AppError(415, "UNSUPPORTED_AUDIO", "Unsupported audio file type")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    final_name = f"audio_{uuid4().hex}{suffix}"
    final_path = UPLOAD_DIR / final_name
    temp_path = final_path.with_suffix(final_path.suffix + ".part")
    total = 0
    header = b""
    try:
        with temp_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                if not header:
                    header = chunk[:32]
                total += len(chunk)
                if total > settings.max_audio_upload_bytes:
                    raise AppError(413, "AUDIO_TOO_LARGE", "Audio file is too large")
                output.write(chunk)
        if not _valid_audio_signature(suffix, header):
            raise AppError(415, "INVALID_AUDIO", "Audio content does not match its extension")
        temp_path.replace(final_path)
    finally:
        temp_path.unlink(missing_ok=True)
        await file.close()
    return AudioUploadResponse(
        audioUrl=f"/uploads/audio/{final_name}",
        audioFormat=suffix.removeprefix("."),
        size=total,
    )


@router.post("/asr", response_model=ASRResponse)
async def asr(req: ASRRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    result = await asr_transcribe(
        req.roomId, user["userId"], req.channel, req.audioUrl,
        audio_format=req.audioFormat, text_hint=req.textHint,
    )
    if result is None:
        raise AppError(404, "ROOM_NOT_FOUND", "导览房间不存在")
    if not result.get("success", True):
        error = str(result.get("error", "ASR failed"))
        if "Unsupported audio format" in error:
            raise AppError(422, "UNSUPPORTED_AUDIO_FORMAT", "暂不支持这种录音格式")
        raise AppError(503, "ASR_UNAVAILABLE", "语音识别服务暂时不可用")
    return ASRResponse(
        text=result["text"], confidence=result["confidence"], warning=result.get("warning")
    )


@router.post("/tts", response_model=TTSResponse)
async def tts(req: TTSRequest, user: dict = Depends(get_current_user)):
    enforce_rate_limit("tts", user["userId"], 30, 60)
    result = await tts_synthesize(req.text, req.voice, req.speed, req.audioFormat)
    if not result.get("success", True):
        error = str(result.get("error", "TTS failed"))
        if "Unsupported audio format" in error or "Text is empty" in error:
            raise AppError(422, "INVALID_TTS_REQUEST", "讲解内容或音频格式不正确")
        raise AppError(503, "TTS_UNAVAILABLE", "讲解语音暂时无法播放")
    return TTSResponse(
        audioUrl=result["audioUrl"], duration=result["duration"], warning=result.get("warning")
    )
