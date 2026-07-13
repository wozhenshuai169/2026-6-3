from time import perf_counter

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.schemas.vision import VisionRecognizeRequest, VisionRecognizeResponse
from app.services.stats import record_event
from app.services.vision import recognize_image

router = APIRouter(prefix="/api/vision")


@router.post("/recognize", response_model=VisionRecognizeResponse)
async def vision_recognize(req: VisionRecognizeRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    enforce_rate_limit("vision", user["userId"], 20, 60)
    started = perf_counter()
    try:
        result = await recognize_image(req.roomId, user["userId"], req.imageUrl, req.currentSpotId)
        if result is None:
            record_event(
                "vision_recognize", success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": req.roomId, "error": "room_not_found"},
            )
            raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
        if result.get("providerError"):
            raise AppError(503, "VISION_UNAVAILABLE", "Vision provider is unavailable")
        record_event(
            "vision_recognize", success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": req.roomId,
                "spotId": result.get("recognizedSpot", {}).get("spotId"),
                "currentSpot": req.currentSpotId,
            },
        )
        return VisionRecognizeResponse(**result)
    except AppError:
        raise
    except Exception as exc:
        record_event(
            "vision_recognize", success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": req.roomId, "error": str(exc)},
        )
        raise AppError(503, "VISION_UNAVAILABLE", "Vision provider is unavailable") from exc
