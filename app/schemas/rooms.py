from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audio import VoiceName


class CreateRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roomName: str = Field(min_length=1, max_length=100)
    scenicAreaId: str = Field(min_length=1, max_length=100)
    routeId: str = Field(min_length=1, max_length=100)


class CreateRoomResponse(BaseModel):
    roomId: str
    status: str


class JoinRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pass


class JoinRoomResponse(BaseModel):
    roomId: str
    userId: str
    status: str


class MemberSchema(BaseModel):
    userId: str
    userName: str


class RoomStatusResponse(BaseModel):
    roomId: str
    leaderId: str
    roomName: str
    scenicAreaId: str
    routeId: str
    members: list[MemberSchema]
    currentSpot: str
    status: str


class UpdateSpotRequest(BaseModel):
    spotId: str = Field(min_length=1, max_length=100)


class UpdateSpotResponse(BaseModel):
    roomId: str
    currentSpot: str
    status: str


class StartNarrationRequest(BaseModel):
    spotId: str = Field(min_length=1, max_length=100)
    voice: VoiceName = "guide_female"


class StartNarrationResponse(BaseModel):
    roomId: str
    spotId: str
    narrationId: str
    text: str
    audioUrl: str
    duration: float = 0.0
    voice: VoiceName = "guide_female"
    status: str = "speaking"
    llmProvider: str = "deepseek"
    audioProvider: str = "edge-tts"


class UpdateRoomStatusRequest(BaseModel):
    status: Literal["active", "paused", "ended"]


class UpdateRoomStatusResponse(BaseModel):
    roomId: str
    status: str


class TransferLeaderRequest(BaseModel):
    userId: str


class MemberActionResponse(BaseModel):
    roomId: str
    userId: str
    status: str
