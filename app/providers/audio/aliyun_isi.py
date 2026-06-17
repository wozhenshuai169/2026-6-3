"""阿里云智能语音交互 ISI Provider —— HMAC-SHA1 签名，RESTful API 调用。

ASR（录音文件识别）: https://nlsapi.aliyun.com/transcriptions
TTS（语音合成）:     http://nlsapi.aliyun.com/speak
"""

import hashlib
import hmac
import base64
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 上传目录
UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"


def _gmt_time() -> str:
    """生成 GMT 格式当前时间。"""
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def _md5_base64(body: str) -> str:
    """计算 body 的 MD5 并 Base64 编码。"""
    digest = hashlib.md5(body.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("utf-8")


def _hmac_sha1_base64(text: str, secret: str) -> str:
    """HMAC-SHA1 签名并 Base64 编码。"""
    sig = hmac.new(secret.encode("utf-8"), text.encode("utf-8"), hashlib.sha1)
    return base64.b64encode(sig.digest()).decode("utf-8")


def _sign_request(method: str, accept: str, content_type: str, body: str) -> dict[str, str]:
    """生成 HMAC-SHA1 鉴权请求头。"""
    secret = settings.isi_access_key_secret
    ak_id = settings.isi_access_key_id
    gmt = _gmt_time()
    body_md5 = _md5_base64(body) if body else _md5_base64("")

    str_to_sign = f"{method}\n{accept}\n{body_md5}\n{content_type}\n{gmt}"
    signature = _hmac_sha1_base64(str_to_sign, secret)

    return {
        "Accept": accept,
        "Content-Type": content_type,
        "Date": gmt,
        "Authorization": f"Dataplus {ak_id}:{signature}",
    }


class AliyunISIProvider:
    provider_name = "aliyun_isi"
    """阿里云智能语音交互 Provider —— ASR + TTS。"""

    def __init__(self) -> None:
        self._app_key = settings.isi_app_key
        logger.info("[ISI] Provider initialized (app_key=%s)", self._app_key)

    # ── ASR 录音文件识别 ────────────────────────────────

    async def asr_transcribe(
        self,
        audio_url: str,
        audio_format: str = "wav",
        text_hint: str = "",
        current_spot: str = "",
    ) -> dict:
        """提交录音文件识别任务并轮询获取结果。

        Args:
            audio_url: 音频文件的公网可访问 URL（需 OSS 或公网地址）
            audio_format: wav / mp3

        Returns:
            {"text": "...", "confidence": 0.95, "success": True}
        """
        # 如果音频 URL 是本地路径，因 ISI 无法访问，降级到提示
        if not (audio_url.startswith("http://") or audio_url.startswith("https://")):
            logger.warning("[ISI ASR] audio_url is not a public URL, ISI cannot access it")
            return {"text": "", "confidence": 0.0, "success": False,
                    "error": "ISI 需要公网可访问的音频链接（OSS/公网URL）"}

        # 1. 提交识别任务
        url = "https://nlsapi.aliyun.com/transcriptions"
        body = json.dumps({"app_key": self._app_key, "oss_link": audio_url})
        headers = _sign_request("POST", "application/json", "application/json", body)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers, content=body)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("id", "")
                if not task_id:
                    return {"text": "", "confidence": 0.0, "success": False,
                            "error": f"提交任务失败: {data}"}
                logger.info("[ISI ASR] Task submitted, id=%s", task_id)
            except httpx.HTTPError as e:
                logger.error("[ISI ASR] Submit error: %s", e)
                return {"text": "", "confidence": 0.0, "success": False,
                        "error": str(e)}

            # 2. 轮询结果（最多 60 次 * 1s）
            for attempt in range(60):
                import asyncio
                await asyncio.sleep(1)
                get_url = f"{url}/{task_id}"
                get_headers = _sign_request(
                    "GET", "application/json", "application/json", ""
                )
                try:
                    gr = await client.get(get_url, headers=get_headers)
                    gr.raise_for_status()
                    result = gr.json()
                    status = result.get("status", "")
                    if status == "SUCCESS":
                        sentences = result.get("result", {}).get("sentences", [])
                        text = "".join(s.get("text", "") for s in sentences)
                        confidence = (
                            sum(s.get("confidence", 0) for s in sentences) / len(sentences)
                            if sentences else 0.0
                        )
                        logger.info("[ISI ASR] Completed, text=%s", text[:80])
                        return {"text": text, "confidence": round(confidence, 4),
                                "success": True, "format": audio_format}
                    elif status in ("FAILED", "ERROR"):
                        logger.error("[ISI ASR] Task failed: %s", result)
                        return {"text": "", "confidence": 0.0, "success": False,
                                "error": str(result.get("message", "unknown error"))}
                except httpx.HTTPError as e:
                    logger.warning("[ISI ASR] Poll attempt %d error: %s", attempt + 1, e)

        return {"text": "", "confidence": 0.0, "success": False,
                "error": "ASR 识别超时（60秒）"}

    # ── TTS 语音合成 ────────────────────────────────────

    async def tts_synthesize(
        self,
        text: str,
        voice: str = "xiaoyun",
        speed: float = 1.0,
        audio_format: str = "mp3",
    ) -> dict:
        """语音合成：文本 → 音频文件。

        Args:
            text: 要合成的文本（≤ 2000 字）
            voice: 发音人 xiaoyun(女) / xiaogang(男) / xiaomei(女) / xiaowei(男)
            speed: 语速倍率（-500 ~ 500）
            audio_format: wav / mp3 / pcm

        Returns:
            {"audioUrl": "/uploads/tts/xxx.mp3", "duration": 5.2, "success": True}
        """
        if not text.strip():
            return {"audioUrl": "", "duration": 0.0, "success": False}

        # 语速映射：1.0 → 0, 0.5 → -250, 1.5 → 250
        speech_rate = int((speed - 1.0) * 500)
        speech_rate = max(-500, min(500, speech_rate))

        # 拼接 URL 参数
        params = {
            "encode_type": audio_format,
            "voice_name": voice,
            "volume": "50",
            "sample_rate": "16000",
            "speech_rate": str(speech_rate),
            "pitch_rate": "0",
            "tts_nus": "1",
        }
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"http://nlsapi.aliyun.com/speak?{param_str}"

        accept = f"audio/{audio_format},application/json"
        content_type = "text/plain"
        headers = _sign_request("POST", accept, content_type, text)
        headers["Content-Length"] = str(len(text.encode("utf-8")))

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await client.post(url, headers=headers, content=text.encode("utf-8"))
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("audio/"):
                    # 保存音频文件
                    tts_dir = UPLOADS_DIR / "tts"
                    tts_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"{uuid.uuid4().hex[:12]}.{audio_format}"
                    filepath = tts_dir / filename
                    with open(filepath, "wb") as f:
                        f.write(resp.content)

                    # 估算时长：180ms / 字
                    duration = round(max(0.9, len(text) * 0.18 / speed), 1)
                    audio_url = f"/uploads/tts/{filename}"
                    logger.info("[ISI TTS] Synthesized: %s (%d bytes)", audio_url, len(resp.content))
                    return {
                        "audioUrl": audio_url,
                        "duration": duration,
                        "voice": voice,
                        "format": audio_format,
                        "success": True,
                    }
                else:
                    logger.error("[ISI TTS] Failed: %s — %s", resp.status_code, resp.text[:300])
                    return {"audioUrl": "", "duration": 0.0, "success": False,
                            "error": f"TTS 合成失败: HTTP {resp.status_code}"}
            except httpx.HTTPError as e:
                logger.error("[ISI TTS] Error: %s", e)
                return {"audioUrl": "", "duration": 0.0, "success": False,
                        "error": str(e)}
