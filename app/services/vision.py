"""Vision recognition service."""

import logging

from app.core.config import settings
from app.core.logging import Timer
from app.providers.factory import get_vision
from app.services.rooms import get_room

logger = logging.getLogger(__name__)


async def recognize_image(room_id: str, user_id: str, image_url: str, current_spot_id: str = "") -> dict | None:
    room = get_room(room_id)
    if room is None:
        logger.warning("Vision: room %s not found", room_id)
        return None

    if not settings.enable_vision:
        return {
            "recognizedSpot": {"spotId": "", "spotName": "Vision disabled", "confidence": 0.0},
            "description": "Image recognition is disabled.",
            "relatedSpots": [],
            "visualFeatures": [],
            "category": "unknown",
        }

    hint = current_spot_id or room.get("currentSpot", "")
    provider = get_vision()

    with Timer(logger, f"Vision recognize (hint={hint[:20]})"):
        try:
            result = await provider.recognize(image_url, hint=hint)
        except Exception as e:
            logger.error("Vision provider error: %s", e)
            return {
                "recognizedSpot": {"spotId": "", "spotName": "Recognition failed", "confidence": 0.0},
                "description": f"Image recognition service error: {e}",
                "relatedSpots": [],
                "visualFeatures": [],
                "category": "unknown",
                "providerError": True,
            }

    description = result.description or "No useful visual information was recognized. Please try another angle."
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
        "warning": None if settings.vision_enabled else "Mock vision mode is active.",
    }
