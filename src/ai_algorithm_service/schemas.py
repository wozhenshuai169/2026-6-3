from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Channel = Literal["public", "private", "leader", "system"]
DecisionType = Literal[
    "ignore",
    "public_reply",
    "private_reply",
    "interrupt_and_answer",
    "notify_leader",
    "emergency_alert",
    "summarize_discussion",
]
RiskLevel = Literal["none", "low", "medium", "high"]


class Citation(BaseModel):
    chunkId: str
    title: str
    source: str = "景区资料"
    updatedAt: str | None = None


class TourState(BaseModel):
    roomId: str = "demo-room"
    currentSpotId: str = "main_hall"
    currentRouteId: str = "classic"
    currentSegmentId: str = "segment_01"
    isExplaining: bool = True
    phase: str = "explaining"
    lastQuestion: str | None = None
    locationHint: str | None = None


class TouristProfile(BaseModel):
    touristId: str = "guest"
    memoryTags: dict[str, Any] = Field(default_factory=dict)
    interests: list[str] = Field(default_factory=list)
    companions: list[str] = Field(default_factory=list)
    language: str = "zh-CN"


class AlgorithmRequest(BaseModel):
    roomId: str = "demo-room"
    userId: str = "guest"
    channel: Channel = "public"
    text: str = ""
    imageUrl: str | None = None
    state: TourState = Field(default_factory=TourState)
    profile: TouristProfile = Field(default_factory=TouristProfile)
    authorizationGranted: bool | None = None


class DecisionResult(BaseModel):
    decision: DecisionType
    channel: Channel
    needInterrupt: bool = False
    needLeaderNotify: bool = False
    riskLevel: RiskLevel = "none"
    reason: str
    nextAction: str


class QAResult(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    stateUpdate: dict[str, Any] = Field(default_factory=dict)


class PrivateAssistantResult(BaseModel):
    answer: str
    needAskAuthorization: bool = False
    authorizationText: str | None = None
    leaderMessage: str | None = None
    memoryTags: dict[str, Any] = Field(default_factory=dict)


class VisionResult(BaseModel):
    recognizedObject: str | None = None
    confidence: float = 0.0
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    relatedSpots: list[str] = Field(default_factory=list)
    recommendedAction: str = "ask_for_more_context"


class RouteRecommendation(BaseModel):
    routeId: str
    title: str
    score: float
    reason: str
    tags: list[str] = Field(default_factory=list)


class AlgorithmResponse(BaseModel):
    decision: DecisionResult
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    stateUpdate: dict[str, Any] = Field(default_factory=dict)
    private: PrivateAssistantResult | None = None
    vision: VisionResult | None = None
    routes: list[RouteRecommendation] = Field(default_factory=list)
    memoryTags: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)

