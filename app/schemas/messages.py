from typing import Literal

from pydantic import BaseModel, Field


class MessageCreateRequest(BaseModel):
    content: str = Field(default="", max_length=1000)
    type: Literal["user", "broadcast"] = "user"
    kind: Literal["text", "image", "audio"] = "text"
    mediaUrl: str = Field(default="", max_length=2048)
    fileName: str = Field(default="", max_length=255)
    duration: float = Field(default=0, ge=0, le=3600)


class RoomMessageResponse(BaseModel):
    id: str
    roomId: str
    userId: str
    userName: str
    content: str
    type: str
    timestamp: int
    kind: Literal["text", "image", "audio"] = "text"
    mediaUrl: str = ""
    fileName: str = ""
    duration: float = 0


class MessageListResponse(BaseModel):
    messages: list[RoomMessageResponse]
    nextCursor: str | None = None


class DirectMessageCreateRequest(BaseModel):
    content: str = Field(default="", max_length=1000)
    kind: Literal["text", "image", "audio"] = "text"
    mediaUrl: str = Field(default="", max_length=2048)
    fileName: str = Field(default="", max_length=255)
    duration: float = Field(default=0, ge=0, le=3600)


class DirectMessageResponse(BaseModel):
    id: str
    roomId: str
    senderId: str
    recipientId: str
    senderName: str
    content: str
    kind: Literal["text", "image", "audio"]
    mediaUrl: str
    fileName: str
    duration: float
    timestamp: int


class DirectMessageListResponse(BaseModel):
    messages: list[DirectMessageResponse]
    nextCursor: str | None = None


class ConversationItem(BaseModel):
    conversationId: str
    kind: Literal["group", "direct"]
    title: str
    peerUserId: str | None = None
    peerUserName: str | None = None
    isLeader: bool = False
    latestMessage: str = ""
    latestAt: int = 0
    unreadCount: int = 0


class ConversationListResponse(BaseModel):
    conversations: list[ConversationItem]


class ChatMediaUploadResponse(BaseModel):
    mediaUrl: str
    kind: Literal["image", "audio"]
    fileName: str
    duration: float = 0
