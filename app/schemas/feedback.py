from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    roomId: str
    userId: str
    score: int = Field(ge=1, le=5)
    scene: str = Field(min_length=1, max_length=50)


class FeedbackResponse(BaseModel):
    feedbackId: str
    score: int
    status: str
