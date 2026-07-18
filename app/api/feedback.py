from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback import upsert_feedback
from app.services.stats import record_event

router = APIRouter(prefix="/api")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(req: FeedbackRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    result = upsert_feedback(
        req.roomId, user["userId"], req.score, req.scene, req.comment, req.tags
    )
    record_event(
        "feedback",
        payload={
            "roomId": req.roomId,
            "score": req.score,
            "scene": req.scene,
            "tags": req.tags,
            "emotion": result["emotion"],
        },
    )
    return FeedbackResponse(**result)
