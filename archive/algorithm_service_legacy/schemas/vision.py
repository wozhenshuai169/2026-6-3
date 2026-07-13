from __future__ import annotations

from pydantic import BaseModel


class VisionRequest(BaseModel):
    roomId: str
    userId: str
    imageUrl: str
    context: dict = {}


class VisionResponse(BaseModel):
    sceneName: str
    description: str
    tags: list[str] = []
    stateUpdate: dict = {}
