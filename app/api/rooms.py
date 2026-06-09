from fastapi import APIRouter, HTTPException

from app.schemas.avatar import AvatarStateResponse
from app.schemas.rooms import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    RoomStatusResponse,
    UpdateSpotRequest,
    UpdateSpotResponse,
)
from app.services.rooms import create_room, get_avatar_state, get_room, join_room, update_current_spot
from app.services.stats import record_event
from app.services.users import get_user_by_token

router = APIRouter(prefix="/api")


@router.post("/rooms", response_model=CreateRoomResponse)
async def create(req: CreateRoomRequest):
    user = get_user_by_token(req.token)
    if user is None:
        record_event("create_room", success=False, payload={"error": "invalid_token"})
        raise HTTPException(status_code=401, detail="Invalid token")
    room = create_room(user["userId"])
    record_event("create_room", success=True, payload={"roomId": room["roomId"], "leaderId": user["userId"]})
    return CreateRoomResponse(roomId=room["roomId"], status="created")


@router.get("/rooms/{roomId}", response_model=RoomStatusResponse)
async def get_status(roomId: str):
    room = get_room(roomId)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomStatusResponse(
        roomId=room["roomId"],
        members=room["members"],
        currentSpot=room["currentSpot"],
        status=room["status"],
    )


@router.post("/rooms/{roomId}/join", response_model=JoinRoomResponse)
async def join(roomId: str, req: JoinRoomRequest):
    room, user_id, _ = join_room(roomId, req.token)
    if room is None:
        record_event("join_room", success=False, payload={"roomId": roomId, "error": "room_not_found"})
        raise HTTPException(status_code=404, detail="Room not found")
    if user_id is None:
        record_event("join_room", success=False, payload={"roomId": roomId, "error": "invalid_token"})
        raise HTTPException(status_code=401, detail="Invalid token")
    record_event("join_room", success=True, payload={"roomId": roomId, "userId": user_id})
    return JoinRoomResponse(roomId=roomId, userId=user_id, status="joined")


@router.post("/rooms/{roomId}/current-spot", response_model=UpdateSpotResponse)
async def update_spot(roomId: str, req: UpdateSpotRequest):
    room = update_current_spot(roomId, req.spotId)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    record_event("update_spot", success=True, payload={"roomId": roomId, "spotId": req.spotId})
    return UpdateSpotResponse(roomId=roomId, currentSpot=req.spotId, status="updated")


@router.get("/rooms/{roomId}/avatar-state", response_model=AvatarStateResponse)
async def avatar_state(roomId: str):
    state = get_avatar_state(roomId)
    if state is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return AvatarStateResponse(**state)
