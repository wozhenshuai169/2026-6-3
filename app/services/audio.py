"""Audio services backed by configured providers and stable /uploads URLs."""

import logging
from pathlib import Path

from app.core.config import settings
from app.core.logging import Timer
from app.providers.factory import get_audio
from app.services.rooms import get_room

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {"wav", "mp3", "webm", "ogg", "m4a"}
UPLOADS_TTS_DIR = Path("uploads") / "tts"


def _validate_format(audio_format: str | None = None) -> str:
    fmt = (audio_format or "wav").lower().strip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported audio format: {fmt}; supported: {', '.join(sorted(SUPPORTED_FORMATS))}")
    return fmt


def _uploaded_file_from_url(audio_url: str) -> Path | None:
    prefix = "/uploads/tts/"
    if not audio_url.startswith(prefix):
        return None
    return UPLOADS_TTS_DIR / audio_url.removeprefix(prefix)


def _provider_audio_url(audio_url: str) -> str:
    """Turn an authenticated local upload path into a provider-readable URL."""
    if audio_url.startswith(("http://", "https://")):
        return audio_url
    if audio_url.startswith("/uploads/") and settings.public_base_url:
        return f"{settings.public_base_url.rstrip('/')}{audio_url}"
    return audio_url


async def asr_transcribe(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    room = get_room(room_id)
    if room is None:
        logger.warning("ASR: room %s not found", room_id)
        return None

    try:
        fmt = _validate_format(audio_format)
    except ValueError as e:
        logger.warning("ASR format error: %s", e)
        return {
            "text": "",
            "confidence": 0.0,
            "success": False,
            "format": audio_format or "unknown",
            "error": str(e),
        }

    if not settings.enable_asr:
        return {"text": "", "confidence": 0.0, "success": False, "format": fmt, "error": "语音识别服务未启用"}
    if not settings.audio_provider_enabled:
        return {
            "text": "",
            "confidence": 0.0,
            "success": False,
            "format": fmt,
            "error": "语音识别服务未配置",
        }

    with Timer(logger, f"ASR '{audio_url[-30:]}'"):
        try:
            result = await get_audio().asr_transcribe(
                audio_url=_provider_audio_url(audio_url),
                audio_format=fmt,
                text_hint=text_hint or "",
                current_spot=room.get("currentSpot", ""),
            )
        except Exception as e:
            logger.error("ASR provider error: %s", e)
            result = {
                "text": "",
                "confidence": 0.0,
                "success": False,
                "format": fmt,
                "error": f"ASR error: {e}",
            }

    result["format"] = fmt
    result["warning"] = None if settings.audio_provider_enabled else "语音识别服务未配置。"
    return result


async def tts_synthesize(
    text: str,
    voice: str = "guide_female",
    speed: float = 1.0,
    audio_format: str = "mp3",
    room_id: str | None = None,
) -> dict:
    if not text.strip():
        return {
            "audioUrl": "",
            "duration": 0.0,
            "voice": voice,
            "format": audio_format,
            "success": False,
            "error": "Text is empty",
        }

    if not settings.enable_tts:
        logger.info("TTS disabled by config")
        return {
            "audioUrl": "",
            "duration": 0.0,
            "voice": voice,
            "format": audio_format,
            "success": False,
            "error": "讲解语音服务未启用",
        }
    if not settings.audio_provider_enabled:
        return {
            "audioUrl": "",
            "duration": 0.0,
            "voice": voice,
            "format": audio_format,
            "success": False,
            "error": "讲解语音服务未配置",
        }

    try:
        fmt = _validate_format(audio_format)
    except ValueError as e:
        return {
            "audioUrl": "",
            "duration": 0.0,
            "voice": voice,
            "format": audio_format,
            "success": False,
            "error": str(e),
        }

    with Timer(logger, f"TTS '{text[:30]}...'"):
        try:
            result = await get_audio().tts_synthesize(text=text, voice=voice, speed=speed, audio_format=fmt)
        except Exception as e:
            logger.error("TTS provider error: %s", e)
            result = {
                "audioUrl": "",
                "duration": 0.0,
                "voice": voice,
                "format": fmt,
                "success": False,
                "error": f"TTS error: {e}",
            }

    if result.get("success", True):
        provider_url = result.get("audioUrl", "")
        provider_path = _uploaded_file_from_url(provider_url) if provider_url else None
        remote_audio = provider_url.startswith(("http://", "https://"))
        if remote_audio or (
            provider_path and provider_path.exists() and provider_path.stat().st_size > 0
        ):
            result["audioUrl"] = provider_url
        else:
            logger.error("TTS provider returned a missing or unreadable audio file: %s", provider_url)
            result.update(
                {
                    "audioUrl": "",
                    "duration": 0.0,
                    "success": False,
                    "error": "讲解语音文件生成失败",
                }
            )

    result["warning"] = None if settings.audio_provider_enabled else "讲解语音服务未配置。"

    return result
