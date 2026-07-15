from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


FeedbackTag = Literal["讲解内容", "语音体验", "路线推荐", "服务设施", "图片识别", "其他"]


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roomId: str
    userId: str
    score: int = Field(ge=1, le=5)
    scene: str = Field(min_length=1, max_length=50)
    comment: str = Field(default="", max_length=500)
    tags: list[FeedbackTag] = Field(default_factory=list, max_length=5)


class FeedbackResponse(BaseModel):
    feedbackId: str
    score: int
    comment: str = ""
    tags: list[FeedbackTag] = Field(default_factory=list)
    emotion: Literal["positive", "neutral", "negative"]
    status: str
