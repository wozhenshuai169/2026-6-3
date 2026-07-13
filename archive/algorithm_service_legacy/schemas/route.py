from __future__ import annotations

from pydantic import BaseModel


class RouteRecommendRequest(BaseModel):
    roomId: str
    currentSpot: str = ""
    preferences: list[str] = []
    context: dict = {}


class RouteRecommendResponse(BaseModel):
    recommendedRouteId: str
    reason: str
    alternatives: list[dict] = []
    stateUpdate: dict = {}
