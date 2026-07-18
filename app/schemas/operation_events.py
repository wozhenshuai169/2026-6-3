from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal["route_closed", "weather_alert", "crowd_warning", "announcement", "facility_closed"]
Severity = Literal["info", "warning", "critical"]
EventStatus = Literal["active", "resolved", "expired"]


class CreateOperationEventRequest(BaseModel):
    scenicAreaId: str = Field(min_length=1, max_length=100)
    eventType: EventType
    severity: Severity = "info"
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=1000)
    affectedSpotIds: list[str] = Field(default_factory=list, max_length=30)
    affectedRouteIds: list[str] = Field(default_factory=list, max_length=30)
    validUntil: int | None = Field(default=None, ge=0)


class UpdateOperationEventRequest(BaseModel):
    status: EventStatus


class OperationEventResponse(BaseModel):
    eventId: str
    scenicAreaId: str
    eventType: EventType
    severity: Severity
    title: str
    content: str
    affectedSpotIds: list[str] = Field(default_factory=list)
    affectedRouteIds: list[str] = Field(default_factory=list)
    status: EventStatus
    validFrom: int
    validUntil: int | None = None
    createdAt: int
    updatedAt: int
