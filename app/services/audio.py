from app.services.rooms import get_room


def asr_transcribe(room_id: str, user_id: str, channel: str, audio_url: str) -> dict | None:
    """Mock ASR：根据房间当前景点生成模拟的语音识别文本"""
    room = get_room(room_id)
    if room is None:
        return None

    spot = room.get("currentSpot", "")
    if spot:
        text = f"请问{spot}有什么历史故事？"
    else:
        text = "这个景区有什么值得看的？"

    return {"text": text, "confidence": 0.92}


def tts_synthesize(text: str, voice: str = "guide_female", speed: float = 1.0) -> dict:
    """Mock TTS：根据文本长度估算时长，返回模拟音频URL"""
    duration = max(1.0, len(text) * 0.3 / speed)
    audio_url = f"/mock/audio/{abs(hash(text))}.mp3"
    return {"audioUrl": audio_url, "duration": round(duration, 1)}
