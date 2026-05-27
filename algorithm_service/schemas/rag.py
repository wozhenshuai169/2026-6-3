from __future__ import annotations

from pydantic import BaseModel


class ScenicRAGRequest(BaseModel):
    roomId: str
    userId: str
    question: str
    currentSpot: str = ""
    context: dict = {}


class ScenicRAGResponse(BaseModel):
    answer: str
    sources: list[str] = []
    confidence: float = 0.0
    stateUpdate: dict = {}
