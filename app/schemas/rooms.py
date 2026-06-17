from pydantic import BaseModel


class CreateRoomRequest(BaseModel):
    token: str
    roomName: str
    scenicAreaId: str
    routeId: str


class CreateRoomResponse(BaseModel):
    roomId: str
    status: str


class JoinRoomRequest(BaseModel):
    token: str


class JoinRoomResponse(BaseModel):
    roomId: str
    userId: str
    status: str


class MemberSchema(BaseModel):
    userId: str
    userName: str


class RoomStatusResponse(BaseModel):
    roomId: str
    roomName: str = ""
    scenicAreaId: str = ""
    routeId: str = ""
    routeSpotIds: list[str] = []
    members: list[MemberSchema]
    currentSpot: str
    status: str


class UpdateSpotRequest(BaseModel):
    spotId: str


class UpdateSpotResponse(BaseModel):
    roomId: str
    currentSpot: str
    status: str


class AddSpotRequest(BaseModel):
    spotId: str
    position: str = "append"
    source: str | None = None


class AddSpotResponse(BaseModel):
    roomId: str
    routeSpotIds: list[str]
    addedSpotId: str
    status: str


class RoomLogListResponse(BaseModel):
    roomId: str
    items: list[dict]
