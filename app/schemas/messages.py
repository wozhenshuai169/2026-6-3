from typing import Literal

from pydantic import BaseModel, Field


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    type: Literal["user", "broadcast"] = "user"


class RoomMessageResponse(BaseModel):
    id: str
    roomId: str
    userId: str
    userName: str
    content: str
    type: str
    timestamp: int


class MessageListResponse(BaseModel):
    messages: list[RoomMessageResponse]
    nextCursor: str | None = None
