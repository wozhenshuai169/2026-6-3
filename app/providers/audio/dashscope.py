"""Audio Provider —— TTS 使用 Microsoft Edge TTS (免费)，ASR 使用 DashScope Paraformer。

TTS: edge-tts 流式合成 → 保存 mp3 → 返回 URL
ASR: DashScope Paraformer 异步识别（需百炼开通 Paraformer 权限）
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://dashscope.aliyuncs.com"
UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"


# ── edge-tts 音色映射 ──────────────────────────────────

VOICE_MAP = {
    "guide_female": "zh-CN-XiaoxiaoNeural",   # 温柔女声（默认导游）
    "guide_male":   "zh-CN-YunxiNeural",       # 成熟男声
    "xiaoyun":      "zh-CN-XiaoxiaoNeural",
    "xiaogang":     "zh-CN-YunxiNeural",
    "xiaomei":      "zh-CN-XiaoyiNeural",      # 活泼女声
    "xiaowei":      "zh-CN-YunyangNeural",     # 新闻男声
}

class DashScopeAudioProvider:
    """音频 Provider —— edge-tts (TTS) + DashScope Paraformer (ASR)。"""

    def __init__(self) -> None:
        self._api_key = settings.dashscope_api_key or settings.vision_api_key
        self._asr_headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        logger.info("[Audio] Provider initialized (TTS=edge-tts, ASR=Paraformer)")

    # ── TTS 语音合成 (edge-tts) ─────────────────────────

    async def tts_synthesize(
        self,
        text: str,
        voice: str = "guide_female",
        speed: float = 1.0,
        audio_format: str = "mp3",
    ) -> dict:
        """使用 Microsoft Edge TTS 合成语音。

        Args:
            text: 要合成的文本
            voice: 前端音色名 → 映射到 edge-tts 神经语音
            speed: 语速倍率
            audio_format: mp3 (edge-tts 输出 mp3)

        Returns:
            {"audioUrl": "/uploads/tts/xxx.mp3", "duration": 5.2, "success": True}
        """
        if not text.strip():
            return {"audioUrl": "", "duration": 0.0, "voice": voice,
                    "format": audio_format, "success": False}

        edge_voice = VOICE_MAP.get(voice, "zh-CN-XiaoxiaoNeural")
        rate_percent = max(-50, min(100, round((float(speed) - 1.0) * 100)))
        rate = f"{rate_percent:+d}%"

        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, edge_voice, rate=rate)

            tts_dir = UPLOADS_DIR / "tts"
            tts_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{uuid.uuid4().hex[:12]}.mp3"
            filepath = tts_dir / filename

            with open(filepath, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])

            audio_url = f"/uploads/tts/{filename}"
            file_size = filepath.stat().st_size
            duration = round(max(0.9, file_size / 16000), 1)  # 按 16kbps 估算
            logger.info("[TTS] edge-tts synthesized: %s (%d bytes, voice=%s)",
                        audio_url, file_size, edge_voice)
            return {
                "audioUrl": audio_url,
                "duration": duration,
                "voice": voice,
                "format": "mp3",
                "success": True,
            }

        except ImportError:
            logger.error("[TTS] edge-tts not installed. Run: pip install edge-tts")
            return {"audioUrl": "", "duration": 0.0, "voice": voice,
                    "format": audio_format, "success": False,
                    "error": "TTS 引擎未安装 (edge-tts)"}
        except Exception as e:
            logger.error("[TTS] edge-tts error: %s", e)
            return {"audioUrl": "", "duration": 0.0, "voice": voice,
                    "format": audio_format, "success": False, "error": str(e)}

    # ── ASR 语音识别 (Paraformer) ───────────────────────

    async def asr_transcribe(
        self,
        audio_url: str,
        audio_format: str = "wav",
        text_hint: str = "",
        current_spot: str = "",
    ) -> dict:
        """Paraformer 录音文件识别（异步提交 + 轮询）。

        要求: 百炼 API Key 需开通 Paraformer 权限 + 音频文件公网 URL。
        """
        if not (audio_url.startswith("http://") or audio_url.startswith("https://")):
            return {"text": "", "confidence": 0.0, "success": False,
                    "format": audio_format,
                    "error": "Paraformer ASR 需要公网可访问的音频链接"}

        # 提交异步识别任务
        url = f"{BASE_URL}/api/v1/services/audio/asr/transcription"
        headers = {**self._asr_headers, "X-DashScope-Async": "enable"}
        payload = {
            "model": "paraformer-v2",
            "input": {"file_urls": [audio_url]},
            "parameters": {"language_hints": ["zh", "en"], "channel_id": [0]},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("output", {}).get("task_id", "")
                if not task_id:
                    return {"text": "", "confidence": 0.0, "success": False,
                            "format": audio_format,
                            "error": f"获取 task_id 失败: {data}"}
                logger.info("[ASR] Paraformer task submitted: %s", task_id)
            except httpx.HTTPStatusError as e:
                body = e.response.text if e.response else ""
                # 权限不足 → 明确提示
                if "InvalidParameter" in body or "does not support" in body:
                    logger.warning("[ASR] Paraformer not available for this API key")
                    return {"text": "", "confidence": 0.0, "success": False,
                            "format": audio_format,
                            "error": "百炼 Key 未开通 Paraformer ASR 权限"}
                logger.error("[ASR] Submit error: %s", e)
                return {"text": "", "confidence": 0.0, "success": False,
                        "format": audio_format, "error": str(e)}
            except httpx.HTTPError as e:
                logger.error("[ASR] Submit error: %s", e)
                return {"text": "", "confidence": 0.0, "success": False,
                        "format": audio_format, "error": str(e)}

            # 轮询结果（最多 60s）
            task_url = f"{BASE_URL}/api/v1/tasks/{task_id}"
            for _ in range(60):
                await asyncio.sleep(1)
                try:
                    tr = await client.get(task_url, headers=self._asr_headers)
                    tr.raise_for_status()
                    result = tr.json()
                    status = result.get("output", {}).get("task_status", "")
                    if status == "SUCCEEDED":
                        results = result.get("output", {}).get("results", [])
                        texts = []
                        for r in results:
                            t_url = r.get("transcription_url", "")
                            if t_url:
                                ar = await client.get(t_url)
                                ar.raise_for_status()
                                for t in ar.json().get("transcripts", []):
                                    texts.append(t.get("text", ""))
                        text = "".join(texts)
                        logger.info("[ASR] Completed: %s", text[:80])
                        return {"text": text, "confidence": 0.95,
                                "success": True, "format": audio_format}
                    elif status == "FAILED":
                        logger.error("[ASR] Task failed: %s", result)
                        return {"text": "", "confidence": 0.0,
                                "success": False, "format": audio_format,
                                "error": "ASR 识别失败"}
                except httpx.HTTPError:
                    pass

            return {"text": "", "confidence": 0.0, "success": False,
                    "format": audio_format, "error": "ASR 识别超时（60秒）"}
