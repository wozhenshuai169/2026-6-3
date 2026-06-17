from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.schemas.vision import VisionRecognizeRequest, VisionRecognizeResponse
from app.services.rooms import record_vision_log
from app.services.stats import record_event
from app.services.vision import recognize_image

router = APIRouter(prefix="/api/vision")


@router.post("/recognize", response_model=VisionRecognizeResponse)
async def vision_recognize(req: VisionRecognizeRequest):
    started = perf_counter()
    try:
        result = await recognize_image(req.roomId, req.userId, req.imageUrl, req.currentSpotId)
        if result is None:
            record_event(
                "vision_recognize",
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": req.roomId, "error": "room_not_found"},
            )
            raise HTTPException(status_code=404, detail="Room not found")
        record_event(
            "vision_recognize",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": req.roomId,
                "spotId": result.get("recognizedSpot", {}).get("spotId"),
                "currentSpot": req.currentSpotId,
            },
        )
        recognized = result.get("recognizedSpot", {})
        record_vision_log(
            req.roomId,
            {
                "userId": req.userId,
                "imageUrl": req.imageUrl,
                "currentSpotId": req.currentSpotId,
                "recognizedSpot": recognized,
                "confidence": recognized.get("confidence", 0.0),
                "description": result.get("description", ""),
                "category": result.get("category", "unknown"),
            },
        )
        return VisionRecognizeResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        record_event(
            "vision_recognize",
            success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": req.roomId, "error": str(e)},
        )
        raise
