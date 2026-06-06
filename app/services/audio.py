"""音频处理服务 —— ASR + TTS，Provider 模式 + 功能开关 + 异常兜底。"""

import logging

from app.core.config import settings
from app.core.logging import Timer
from app.services.rooms import get_room
from app.providers.factory import get_audio

logger = logging.getLogger(__name__)
SUPPORTED_FORMATS = {"wav", "mp3", "webm", "ogg", "m4a"}
_audio = get_audio()


def _validate_format(audio_format: str | None = None) -> str:
    fmt = (audio_format or "wav").lower().strip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"不支持的音频格式: {fmt}，支持: {', '.join(sorted(SUPPORTED_FORMATS))}")
    return fmt


async def asr_transcribe(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    """语音识别，含格式校验、超时兜底。"""
    room = get_room(room_id)
    if room is None:
        logger.warning("ASR: room %s not found", room_id)
        return None

    try:
        fmt = _validate_format(audio_format)
    except ValueError as e:
        logger.warning("ASR format error: %s", e)
        return {"text": "", "confidence": 0.0, "success": False,
                "format": audio_format or "unknown", "error": str(e)}

    if not settings.enable_asr:
        logger.info("ASR disabled by config, using hint fallback")
        if text_hint and text_hint.strip():
            return {"text": text_hint.strip(), "confidence": 0.7, "success": True, "format": fmt}
        return {"text": "", "confidence": 0.0, "success": False,
                "format": fmt, "error": "ASR 功能已关闭"}

    with Timer(logger, f"ASR '{audio_url[-30:]}'"):
        try:
            result = await _audio.asr_transcribe(
                audio_url=audio_url,
                audio_format=fmt,
                text_hint=text_hint or "",
                current_spot=room.get("currentSpot", ""),
            )
        except Exception as e:
            logger.error("ASR provider error: %s", e)
            result = {"text": "", "confidence": 0.0, "success": False,
                      "format": fmt, "error": f"ASR 异常: {e}"}

    result["format"] = fmt
    return result


async def tts_synthesize(
    text: str,
    voice: str = "guide_female",
    speed: float = 1.0,
    audio_format: str = "mp3",
) -> dict:
    """语音合成，含空文本兜底、engine 降级。"""
    if not text.strip():
        return {"audioUrl": "", "duration": 0.0, "voice": voice,
                "format": audio_format, "success": False,
                "error": "文本为空"}

    if not settings.enable_tts:
        logger.info("TTS disabled by config")
        return {"audioUrl": "", "duration": 0.0, "voice": voice,
                "format": audio_format, "success": False,
                "error": "TTS 功能已关闭"}

    try:
        fmt = _validate_format(audio_format)
    except ValueError as e:
        return {"audioUrl": "", "duration": 0.0, "voice": voice,
                "format": audio_format, "success": False, "error": str(e)}

    with Timer(logger, f"TTS '{text[:30]}...'"):
        try:
            result = await _audio.tts_synthesize(
                text=text, voice=voice, speed=speed, audio_format=fmt,
            )
        except Exception as e:
            logger.error("TTS provider error: %s", e)
            result = {"audioUrl": "", "duration": 0.0, "voice": voice,
                      "format": fmt, "success": False, "error": f"TTS 异常: {e}"}

    return result
