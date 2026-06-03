"""视觉识景服务 —— 通过 Vision Provider 识别图片中的景点。"""

from app.services.rooms import get_room
from app.providers.factory import get_vision


async def recognize_image(room_id: str, user_id: str, image_url: str, current_spot_id: str = "") -> dict | None:
    """图片识景：调用 Vision Provider 返回识别结果。"""
    room = get_room(room_id)
    if room is None:
        return None

    # 优先使用传入的 currentSpotId，否则用房间当前景点
    hint = current_spot_id or room.get("currentSpot", "")

    provider = get_vision()
    result = await provider.recognize(image_url, hint=hint)

    return {
        "recognizedSpot": {
            "spotId": result.spot_id,
            "spotName": result.spot_name,
            "confidence": result.confidence,
        },
        "description": result.description,
        "relatedSpots": result.related_spots,
        "visualFeatures": result.visual_features,
    }
