from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    roomId: str | None = None
    userId: str | None = None
    scene: str | None = None
    score: int = Field(ge=1, le=5)
    comment: str | None = None


class FeedbackResponse(BaseModel):
    feedbackId: str
    status: str
