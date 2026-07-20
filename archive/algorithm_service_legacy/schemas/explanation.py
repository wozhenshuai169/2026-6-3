from __future__ import annotations

from pydantic import BaseModel


class ExplanationRequest(BaseModel):
    roomId: str
    spotId: str
    spotName: str = ""
    style: str = "standard"  # standard | storytelling | kid_friendly
    context: dict = {}


class ExplanationResponse(BaseModel):
    explanation: str
    continuation: str
    ttsText: str
    stateUpdate: dict = {}
