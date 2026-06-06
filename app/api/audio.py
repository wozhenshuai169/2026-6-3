from fastapi import APIRouter, HTTPException

from app.schemas.audio import ASRRequest, ASRResponse, TTSRequest, TTSResponse
from app.services.audio import asr_transcribe, tts_synthesize

router = APIRouter(prefix="/api/audio")


@router.post("/asr", response_model=ASRResponse)
async def asr(req: ASRRequest):
    """语音识别：上传音频URL，返回识别文本"""
    result = await asr_transcribe(
        req.roomId, req.userId, req.channel, req.audioUrl,
        audio_format=req.audioFormat,
        text_hint=req.textHint,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return ASRResponse(text=result["text"], confidence=result["confidence"])


@router.post("/tts", response_model=TTSResponse)
async def tts(req: TTSRequest):
    """语音合成：输入文本，返回合成音频URL"""
    result = await tts_synthesize(req.text, req.voice, req.speed, req.audioFormat)
    return TTSResponse(audioUrl=result["audioUrl"], duration=result["duration"])
