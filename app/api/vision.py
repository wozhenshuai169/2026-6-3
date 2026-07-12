from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.schemas.vision import VisionRecognizeRequest, VisionRecognizeResponse
from app.services.stats import record_event
from app.services.vision import recognize_image

router = APIRouter(prefix="/api/vision")


@router.post("/recognize", response_model=VisionRecognizeResponse)
async def vision_recognize(req: VisionRecognizeRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    started = perf_counter()
    try:
        result = await recognize_image(req.roomId, user["userId"], req.imageUrl, req.currentSpotId)
        if result is None:
            record_event(
                "vision_recognize", success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": req.roomId, "error": "room_not_found"},
            )
            raise HTTPException(status_code=404, detail="Room not found")
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
    except HTTPException:
        raise
    except Exception as exc:
        record_event(
            "vision_recognize", success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": req.roomId, "error": str(exc)},
        )
        raise
