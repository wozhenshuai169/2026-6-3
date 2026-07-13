from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
