"""视觉识景服务 —— 通过 Vision Provider 识别图片中的景点/人物/物体。"""

import logging

from app.core.config import settings
from app.core.logging import Timer, log_model_call
from app.services.rooms import get_room
from app.providers.factory import get_vision

logger = logging.getLogger(__name__)


async def recognize_image(
    room_id: str, user_id: str, image_url: str, current_spot_id: str = "",
) -> dict | None:
    """图片识景：调用 Vision Provider 返回识别结果，含异常兜底。"""
    room = get_room(room_id)
    if room is None:
        logger.warning("Vision: room %s not found", room_id)
        return None

    if not settings.enable_vision:
        return {
            "recognizedSpot": {"spotId": "", "spotName": "视觉功能已关闭", "confidence": 0.0},
            "description": "图片识景功能未开启。",
            "relatedSpots": [], "visualFeatures": [], "category": "unknown",
        }

    hint = current_spot_id or room.get("currentSpot", "")
    provider = get_vision()

    with Timer(logger, f"Vision recognize (hint={hint[:20]})"):
        try:
            result = await provider.recognize(image_url, hint=hint)
        except Exception as e:
            logger.error("Vision provider error: %s", e)
            return {
                "recognizedSpot": {"spotId": "", "spotName": "识别失败", "confidence": 0.0},
                "description": f"图片识别服务异常: {e}",
                "relatedSpots": [], "visualFeatures": [], "category": "unknown",
                "error": str(e),
            }

    # 空结果兜底
    if not result.description:
        result.description = "未能从图片中获取有效信息，请尝试换个角度拍摄。"

    return {
        "recognizedSpot": {
            "spotId": result.spot_id,
            "spotName": result.spot_name,
            "confidence": result.confidence,
        },
        "description": result.description,
        "relatedSpots": result.related_spots,
        "visualFeatures": result.visual_features,
        "category": result.category,
    }
