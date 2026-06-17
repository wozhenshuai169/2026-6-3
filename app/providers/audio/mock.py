"""Mock Audio Provider —— 当 ISI 凭证未配置时降级使用。

ASR: 按音频文件名关键词匹配 demo 语句
TTS: 基于文本哈希生成稳定的 URL
"""

import hashlib
import logging

logger = logging.getLogger(__name__)


class MockAudioProvider:
    provider_name = "mock_audio"
    """Mock 音频：关键词匹配 + 假音频 URL。"""

    def __init__(self) -> None:
        logger.info("[Audio] Using Mock (no ISI credentials configured)")

    # ── ASR ─────────────────────────────────────────────

    async def asr_transcribe(
        self,
        audio_url: str,
        audio_format: str = "wav",
        text_hint: str = "",
        current_spot: str = "",
    ) -> dict:
        """Mock 语音识别：关键词匹配 → demo 文本。"""
        fmt = audio_format.lower() if audio_format else "wav"

        # text_hint 优先
        if text_hint and text_hint.strip():
            return {"text": text_hint.strip(), "confidence": 0.88, "format": fmt}

        # 按音频来源关键词匹配
        source = (audio_url or "").lower()
        demos = [
            (["toilet", "washroom", "restroom", "cesuo", "厕所"], "我想去厕所", 0.84),
            (["lost", "miss", "zoushi", "走散", "找不到"], "我找不到队伍了", 0.86),
            (["tired", "rest", "elderly", "老人", "走不动"], "老人走不动了，附近能休息吗", 0.82),
            (["bell", "zhonglou", "钟楼"], "这张图是不是钟楼", 0.80),
            (["route", "short", "路线", "少走路"], "我想换一条少走路的路线", 0.81),
        ]
        for keywords, text, confidence in demos:
            if any(kw in source for kw in keywords):
                return {"text": text, "confidence": confidence, "format": fmt}

        # 回退：根据当前景点生成通用问句
        if current_spot:
            text = f"请问{current_spot}有什么历史故事？"
        else:
            text = "这个景区有什么值得看的？"
        return {"text": text, "confidence": 0.35, "format": fmt}

    # ── TTS ─────────────────────────────────────────────

    async def tts_synthesize(
        self,
        text: str,
        voice: str = "guide_female",
        speed: float = 1.0,
        audio_format: str = "mp3",
    ) -> dict:
        """Mock 语音合成：SHA1 哈希 → 伪 URL + 时长估算。"""
        if not text.strip():
            return {"audioUrl": "", "duration": 0.0, "voice": voice,
                    "format": audio_format, "success": False}

        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        url = f"/static/tts/{digest}.{audio_format}"
        duration = round(max(0.9, len(text) * 0.18 / speed), 1)

        return {
            "audioUrl": url,
            "duration": duration,
            "voice": voice,
            "format": audio_format,
            "success": True,
        }
