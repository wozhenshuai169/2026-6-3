from fastapi import APIRouter

from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.stats import record_event, record_feedback

router = APIRouter(prefix="/api/feedback")


@router.post("", response_model=FeedbackResponse)
async def create_feedback(req: FeedbackRequest):
    item = record_feedback(req.score, req.roomId, req.userId, req.scene, req.comment)
    record_event(
        "feedback",
        success=True,
        payload={"roomId": req.roomId, "userId": req.userId, "score": req.score, "scene": req.scene},
    )
    return FeedbackResponse(feedbackId=item["feedbackId"], status="created")
