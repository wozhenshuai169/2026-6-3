"""Local-friendly speech provider using Qwen-ASR and Microsoft Edge TTS."""

import base64
import logging
import mimetypes
import uuid
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"

VOICE_MAP = {
    "guide_female": "zh-CN-XiaoxiaoNeural",
    "guide_male": "zh-CN-YunxiNeural",
    "xiaoyun": "zh-CN-XiaoxiaoNeural",
    "xiaogang": "zh-CN-YunxiNeural",
    "xiaomei": "zh-CN-XiaoyiNeural",
    "xiaowei": "zh-CN-YunyangNeural",
}


class DashScopeAudioProvider:
    """Speech provider for short visitor questions and guide narration."""

    def __init__(self) -> None:
        self._api_key = settings.dashscope_api_key or settings.vision_api_key
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        logger.info("[Audio] Provider initialized (ASR=Qwen3-ASR, TTS=Edge TTS)")

    async def tts_synthesize(
        self,
        text: str,
        voice: str = "guide_female",
        speed: float = 1.0,
        audio_format: str = "mp3",
    ) -> dict:
        if not text.strip():
            return {
                "audioUrl": "", "duration": 0.0, "voice": voice,
                "format": audio_format, "success": False, "error": "Text is empty",
            }

        edge_voice = VOICE_MAP.get(voice, VOICE_MAP["guide_female"])
        rate_percent = max(-50, min(100, round((float(speed) - 1.0) * 100)))
        rate = f"{rate_percent:+d}%"
        tts_dir = UPLOADS_DIR / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex[:12]}.mp3"
        filepath = tts_dir / filename

        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, edge_voice, rate=rate)
            with filepath.open("wb") as output:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        output.write(chunk["data"])
            file_size = filepath.stat().st_size
            if file_size <= 0:
                raise ValueError("TTS returned an empty audio file")
        except ImportError:
            logger.error("[TTS] edge-tts is not installed")
            return {
                "audioUrl": "", "duration": 0.0, "voice": voice,
                "format": audio_format, "success": False,
                "error": "TTS engine is not installed (edge-tts)",
            }
        except Exception as exc:
            filepath.unlink(missing_ok=True)
            logger.error("[TTS] edge-tts failed: %s", exc)
            return {
                "audioUrl": "", "duration": 0.0, "voice": voice,
                "format": audio_format, "success": False, "error": str(exc),
            }

        audio_url = f"/uploads/tts/{filename}"
        duration = round(max(0.9, file_size / 16000), 1)
        logger.info("[TTS] Synthesized %s (%d bytes, voice=%s)", audio_url, file_size, edge_voice)
        return {
            "audioUrl": audio_url,
            "duration": duration,
            "voice": voice,
            "format": "mp3",
            "success": True,
        }

    async def asr_transcribe(
        self,
        audio_url: str,
        audio_format: str = "wav",
        text_hint: str = "",
        current_spot: str = "",
    ) -> dict:
        """Transcribe a short local upload or public URL with Qwen3-ASR-Flash."""
        if not self._api_key:
            return self._asr_error(audio_format, "百炼语音识别 API Key 未配置")

        try:
            audio_input = self._encode_audio_input(audio_url, audio_format)
        except (OSError, ValueError) as exc:
            return self._asr_error(audio_format, str(exc))

        del text_hint, current_spot
        messages = [{
            "role": "user",
            "content": [{"type": "input_audio", "input_audio": {"data": audio_input}}],
        }]
        payload = {
            "model": settings.asr_model,
            "messages": messages,
            "stream": False,
            "asr_options": {"enable_itn": True},
        }
        base_url = (settings.vision_base_url or BASE_URL).rstrip("/")

        try:
            async with httpx.AsyncClient(timeout=settings.asr_timeout) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            logger.warning("[ASR] Qwen-ASR request timed out")
            return self._asr_error(audio_format, "语音识别请求超时")
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("[ASR] Qwen-ASR request failed: %s", exc)
            return self._asr_error(audio_format, f"语音识别请求失败: {exc}")

        choices = data.get("choices") or []
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )
        transcript = str(content).strip()
        if not transcript:
            return self._asr_error(audio_format, "语音识别未返回文字")

        logger.info("[ASR] Qwen-ASR completed: %s", transcript[:80])
        return {
            "text": transcript,
            "confidence": 0.0,
            "success": True,
            "format": audio_format,
            "warning": "识别模型未返回置信度",
        }

    @staticmethod
    def _encode_audio_input(audio_url: str, audio_format: str) -> str:
        if audio_url.startswith(("http://", "https://")):
            return audio_url

        path = Path(audio_url).resolve()
        upload_root = UPLOADS_DIR.resolve()
        try:
            path.relative_to(upload_root)
        except ValueError as exc:
            raise ValueError("录音文件不在允许的上传目录中") from exc
        if not path.is_file():
            raise ValueError("录音文件不存在")
        if path.stat().st_size > settings.max_audio_upload_bytes:
            raise ValueError("录音文件超过大小限制")

        mime = mimetypes.guess_type(path.name)[0] or f"audio/{audio_format}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def _asr_error(audio_format: str, error: str) -> dict:
        return {
            "text": "",
            "confidence": 0.0,
            "success": False,
            "format": audio_format,
            "error": error,
        }
