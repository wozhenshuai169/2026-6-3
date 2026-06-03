"""音频处理服务 —— ASR 语音识别 + TTS 语音合成。

对齐 src/ai_algorithm_service/voice.py 的 VoiceAdapter 模式：
- ASR 支持 text_hint、格式校验、demo 关键词匹配
- TTS 基于文本哈希生成 URL，估算时长
"""

import hashlib

from app.services.rooms import get_room

# 支持的音频格式
SUPPORTED_FORMATS = {"wav", "mp3"}


def _validate_format(audio_format: str | None = None) -> str:
    """校验音频格式，非法格式抛 ValueError。"""
    fmt = (audio_format or "wav").lower().strip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError("只支持 wav / mp3 音频格式")
    return fmt


def asr_transcribe(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    """语音识别：提交音频 URL，返回识别文本。

    对齐 VoiceAdapter.asr()：
    - 有 text_hint 时置信度 0.88
    - 按音频文件名关键词匹配 demo 语句
    - 未匹配时返回低置信度
    """
    room = get_room(room_id)
    if room is None:
        return None

    try:
        fmt = _validate_format(audio_format)
    except ValueError:
        return {"text": "", "confidence": 0.0, "format": audio_format or "unknown", "success": False}

    # text_hint 优先
    if text_hint and text_hint.strip():
        return {"text": text_hint.strip(), "confidence": 0.88, "format": fmt}

    # 按音频来源关键词匹配 demo 语句
    source = (audio_url or "").lower()
    demos = [
        (["toilet", "washroom", "restroom", "cesuo", "厕所"], "我想去厕所", 0.84),
        (["lost", "miss", "zoushi", "走散", "找不到"], "我找不到队伍了", 0.86),
        (["tired", "rest", "elderly", "老人", "走不动"], "老人走不动了，附近能休息吗", 0.82),
        (["bell", "zhonglou", "钟楼"], "这张图是不是钟楼", 0.80),
        (["route", "short", "路线", "少走路"], "我想换一条少走路的路线", 0.81),
    ]
    for keywords, text, confidence in demos:
        if any(keyword in source for keyword in keywords):
            return {"text": text, "confidence": confidence, "format": fmt}

    # 回退：根据房间当前景点生成通用问句
    spot = room.get("currentSpot", "")
    if spot:
        text = f"请问{spot}有什么历史故事？"
    else:
        text = "这个景区有什么值得看的？"

    return {"text": text, "confidence": 0.35, "format": fmt}


def tts_synthesize(
    text: str,
    voice: str = "guide_female",
    speed: float = 1.0,
    audio_format: str = "mp3",
) -> dict:
    """语音合成：输入文本，返回合成音频 URL。

    对齐 VoiceAdapter.tts()：
    - 按 SHA1 哈希生成稳定的 URL
    - 按文本长度（180ms/字）估算时长
    """
    if not text.strip():
        return {
            "audioUrl": "",
            "duration": 0.0,
            "voice": voice,
            "format": audio_format,
            "success": False,
        }

    try:
        fmt = _validate_format(audio_format)
    except ValueError:
        return {
            "audioUrl": "",
            "duration": 0.0,
            "voice": voice,
            "format": audio_format,
            "success": False,
        }

    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    url = f"/static/tts/{digest}.{fmt}"
    duration_ms = max(900, min(12000, len(text) * 180))
    duration = round(duration_ms / 1000.0 / speed, 1)

    return {
        "audioUrl": url,
        "duration": duration,
        "voice": voice,
        "format": fmt,
        "success": True,
    }
