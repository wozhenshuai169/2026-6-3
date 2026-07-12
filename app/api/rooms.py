from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import authenticate_token, bearer_scheme, get_current_user, require_room_member
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
from app.services.rooms import create_room, get_avatar_state, join_room, update_current_spot
from app.services.stats import record_event

router = APIRouter(prefix="/api")


def _request_user(
    credentials: HTTPAuthorizationCredentials | None,
    fallback_token: str | None,
) -> dict:
    return authenticate_token(credentials.credentials if credentials else fallback_token)


@router.post("/rooms", response_model=CreateRoomResponse)
async def create(
    req: CreateRoomRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    user = _request_user(credentials, req.token)
    if user.get("role") not in {"guide", "admin"}:
        raise HTTPException(status_code=403, detail="Guide role required")
    room = create_room(user, req.roomName, req.scenicAreaId, req.routeId)
    record_event("create_room", success=True, payload={"roomId": room["roomId"], "leaderId": user["userId"]})
    return CreateRoomResponse(roomId=room["roomId"], status="created")


@router.get("/rooms/{roomId}", response_model=RoomStatusResponse)
async def get_status(roomId: str, user: dict = Depends(get_current_user)):
    room = require_room_member(roomId, user)
    return RoomStatusResponse(**room)


@router.post("/rooms/{roomId}/join", response_model=JoinRoomResponse)
async def join(
    roomId: str,
    req: JoinRoomRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    token = credentials.credentials if credentials else req.token
    user = authenticate_token(token)
    room, user_id, _ = join_room(roomId, token or "")
    if room is None:
        record_event("join_room", success=False, payload={"roomId": roomId, "error": "room_not_found"})
        raise HTTPException(status_code=404, detail="Room not found")
    record_event("join_room", success=True, payload={"roomId": roomId, "userId": user["userId"]})
    return JoinRoomResponse(roomId=roomId, userId=user_id or user["userId"], status="joined")


@router.post("/rooms/{roomId}/current-spot", response_model=UpdateSpotResponse)
async def update_spot(
    roomId: str,
    req: UpdateSpotRequest,
    user: dict = Depends(get_current_user),
):
    require_room_member(roomId, user, leader_only=True)
    room = update_current_spot(roomId, req.spotId)
    record_event("update_spot", success=True, payload={"roomId": roomId, "spotId": req.spotId})
    return UpdateSpotResponse(roomId=roomId, currentSpot=room["currentSpot"], status="updated")


@router.get("/rooms/{roomId}/avatar-state", response_model=AvatarStateResponse)
async def avatar_state(roomId: str, user: dict = Depends(get_current_user)):
    require_room_member(roomId, user)
    state = get_avatar_state(roomId)
    return AvatarStateResponse(**state)
