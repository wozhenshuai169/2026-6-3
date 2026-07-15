"""Vision recognition service."""

import logging

from app.core.config import settings
from app.core.logging import Timer
from app.providers.factory import get_vision
from app.services.algorithm_facade import algorithm_facade
from app.services.knowledge import search_knowledge
from app.services.users import get_user_memory_tags
from app.services.rooms import get_room

logger = logging.getLogger(__name__)


async def recognize_image(room_id: str, user_id: str, image_url: str, current_spot_id: str = "") -> dict | None:
    room = get_room(room_id)
    if room is None:
        logger.warning("Vision: room %s not found", room_id)
        return None

    if not settings.vision_enabled:
        return {
            "recognizedSpot": {"spotId": "", "spotName": "暂未识别", "confidence": 0.0},
            "description": "图片识别服务未配置。",
            "relatedSpots": [],
            "visualFeatures": [],
            "category": "unknown",
            "providerError": True,
        }

    hint = current_spot_id or room.get("currentSpot", "")
    algorithm_request = algorithm_facade.request(
        room,
        user_id,
        text="介绍这张图",
        input_mode="image",
        image_url=image_url,
        memory_tags=get_user_memory_tags(user_id),
    )
    decision = algorithm_facade.decide(algorithm_request)
    provider = get_vision()

    with Timer(logger, f"Vision recognize (hint={hint[:20]})"):
        try:
            result = await provider.recognize(image_url, hint=hint)
        except Exception as e:
            logger.error("Vision provider error: %s", e)
            return {
                "recognizedSpot": {"spotId": "", "spotName": "暂未识别", "confidence": 0.0},
                "description": "图片识别服务暂时不可用。",
                "relatedSpots": [],
                "visualFeatures": [],
                "category": "unknown",
                "providerError": True,
            }

    description = result.description or "暂时没有识别出有效信息，请换个角度再试。"
    citations: list[dict] = []
    if result.spot_id and result.category == "spot":
        knowledge = search_knowledge(result.spot_name, limit=1, spot_id=result.spot_id)
        citations = [{"title": item["title"], "chunkId": item["chunkId"]} for item in knowledge]
        if knowledge:
            description = f"{description} {knowledge[0]['contentPreview']}"
    return {
        "recognizedSpot": {
            "spotId": result.spot_id,
            "spotName": result.spot_name,
            "confidence": result.confidence,
        },
        "description": description,
        "relatedSpots": result.related_spots,
        "visualFeatures": result.visual_features,
        "category": result.category,
        "warning": None,
        "sources": citations,
        "decision": decision.model_dump(),
    }
