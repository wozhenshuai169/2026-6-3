"""Generate and persist room narration for synchronized guide playback."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError
from app.providers.factory import get_llm
from app.services.audio import tts_synthesize
from app.services.knowledge import search_knowledge
from app.services.rooms import get_room, save_room_narration
from app.services.stats import record_event

logger = logging.getLogger(__name__)

SPOT_NAMES = {
    "lingshan_dazhaobi": "灵山大照壁",
    "jiulong_guanyu": "九龙灌浴",
    "xiangfu_temple": "祥符禅寺",
    "lingshan_buddha": "灵山大佛",
    "lingshan_palace": "灵山梵宫",
    "wuyin_mandala": "五印坛城",
}


async def generate_room_narration(
    room_id: str,
    spot_id: str,
    voice: str = "guide_female",
) -> dict:
    started = perf_counter()
    spot_name = SPOT_NAMES.get(spot_id, spot_id.replace("_", " "))
    try:
        if not settings.deepseek_api_key.strip():
            raise AppError(503, "LLM_NOT_CONFIGURED", "智能讲解服务未配置")
        if not settings.enable_tts or not settings.audio_provider_enabled:
            raise AppError(503, "TTS_NOT_CONFIGURED", "TTS provider is not configured")

        room = get_room(room_id)
        if room is None:
            raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
        if room.get("currentSpot") != spot_id:
            raise AppError(409, "SPOT_CHANGED", "Current spot changed before narration started")

        knowledge = search_knowledge(spot_name, 3, spot_id=spot_id)
        if knowledge:
            context_text = "\n\n".join(
                f"[{item['title']}] {item['contentPreview']}" for item in knowledge
            )
        else:
            context_text = "知识库暂无该景点的直接资料。"

        prompt = (
            "你是灵山胜境的现场中文数字导游。请为团队生成一段可直接朗读的景点讲解词。"
            "长度控制在100到160个汉字，开头自然欢迎游客，语言生动但不夸张，不使用Markdown。"
            "事实优先依据资料；资料不足时只介绍可靠的通用背景，不得编造精确年代、数字或实时安排。\n"
            f"景点：{spot_name}\n资料：\n{context_text}"
        )
        try:
            response = await get_llm().chat(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"请开始讲解{spot_name}。"},
                ],
                temperature=0.4,
                max_tokens=500,
                timeout=settings.request_timeout,
            )
        except Exception as exc:
            logger.error("Room narration DeepSeek request failed: %s", exc)
            raise AppError(503, "LLM_UNAVAILABLE", "智能讲解服务暂时不可用") from exc

        text = (response.content or "").strip()
        if not text:
            raise AppError(503, "LLM_EMPTY_RESPONSE", "智能讲解服务没有返回内容")

        tts = await tts_synthesize(text, voice=voice, speed=1.0, room_id=room_id)
        audio_url = tts.get("audioUrl", "")
        if not tts.get("success", True) or not audio_url:
            raise AppError(
                503,
                "TTS_UNAVAILABLE",
                tts.get("error") or "TTS provider did not return playable audio",
            )

        latest_room = get_room(room_id)
        if latest_room is None or latest_room.get("currentSpot") != spot_id:
            raise AppError(409, "NARRATION_SUPERSEDED", "A newer spot replaced this narration")

        narration_id = uuid4().hex
        duration = float(tts.get("duration", 0.0) or 0.0)
        save_room_narration(room_id, narration_id, text, audio_url, duration)
        result = {
            "roomId": room_id,
            "spotId": spot_id,
            "narrationId": narration_id,
            "text": text,
            "audioUrl": audio_url,
            "duration": duration,
            "voice": voice,
            "status": "speaking",
            "llmProvider": "deepseek",
            "audioProvider": "edge-tts",
        }
        record_event(
            "room_narration",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": room_id,
                "spotId": spot_id,
                "narrationId": narration_id,
                "hasKnowledge": bool(knowledge),
                "hasAudio": True,
                "voice": voice,
                "llmProvider": "deepseek",
                "audioProvider": "edge-tts",
            },
        )
        return result
    except Exception as exc:
        record_event(
            "room_narration",
            success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "spotId": spot_id, "error": str(exc)},
        )
        raise
