from __future__ import annotations

from pydantic import BaseModel


class PrivateAssistantRequest(BaseModel):
    roomId: str
    userId: str
    question: str
    context: dict = {}


class PrivateAssistantResponse(BaseModel):
    answer: str
    needLeaderAuth: bool = False
    notification: str = ""
    stateUpdate: dict = {}
