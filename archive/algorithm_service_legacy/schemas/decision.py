from __future__ import annotations

from pydantic import BaseModel


# ── DecisionRouter ──

class DecisionRequest(BaseModel):
    roomId: str
    userId: str
    event: str  # user_question | spot_reached | idle_timeout | leader_action
    context: dict = {}


class DecisionResponse(BaseModel):
    shouldIntervene: bool
    channel: str  # public | private | none
    shouldInterrupt: bool
    reason: str
