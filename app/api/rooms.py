from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_room_member
from app.core.errors import AppError
from app.schemas.avatar import AvatarStateResponse
from app.schemas.rooms import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    MemberActionResponse,
    RoomStatusResponse,
    TransferLeaderRequest,
    UpdateRoomStatusRequest,
    UpdateRoomStatusResponse,
    UpdateSpotRequest,
    UpdateSpotResponse,
)
from app.services.messages import create_message
from app.services.realtime import room_connections
from app.services.rooms import (
    create_room,
    get_avatar_state,
    join_room,
    leave_room,
    remove_member,
    transfer_leader,
    update_current_spot,
    update_room_status,
)
from app.services.stats import record_event

router = APIRouter(prefix="/api")


async def _broadcast_system(room_id: str, content: str, event_type: str, data: dict) -> None:
    message = create_message(room_id, None, "System", content, "system")
    await room_connections.broadcast(room_id, {"type": "room.message", "data": message})
    await room_connections.broadcast(room_id, {"type": event_type, "data": data})


@router.post("/rooms", response_model=CreateRoomResponse)
async def create(req: CreateRoomRequest, user: dict = Depends(get_current_user)):
    if user.get("role") not in {"guide", "admin"}:
        raise AppError(403, "GUIDE_REQUIRED", "Guide role required")
    room = create_room(user, req.roomName, req.scenicAreaId, req.routeId)
    record_event("create_room", payload={"roomId": room["roomId"], "leaderId": user["userId"]})
    return CreateRoomResponse(roomId=room["roomId"], status="created")


@router.get("/rooms/{roomId}", response_model=RoomStatusResponse)
async def get_status(roomId: str, user: dict = Depends(get_current_user)):
    return RoomStatusResponse(**require_room_member(roomId, user))


@router.post("/rooms/{roomId}/join", response_model=JoinRoomResponse)
async def join(roomId: str, req: JoinRoomRequest, user: dict = Depends(get_current_user)):
    del req
    try:
        room = join_room(roomId, user)
    except ValueError as exc:
        raise AppError(409, "ROOM_NOT_ACTIVE", str(exc)) from exc
    if room is None:
        raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
    record_event("join_room", payload={"roomId": roomId, "userId": user["userId"]})
    await _broadcast_system(
        roomId,
        f"{user['userName']} joined the room.",
        "room.members",
        {"members": room["members"]},
    )
    return JoinRoomResponse(roomId=roomId, userId=user["userId"], status="joined")


@router.delete("/rooms/{roomId}/members/me", response_model=MemberActionResponse)
async def leave(roomId: str, user: dict = Depends(get_current_user)):
    require_room_member(roomId, user)
    try:
        room = leave_room(roomId, user["userId"])
    except ValueError as exc:
        raise AppError(409, "LEADER_CANNOT_LEAVE", str(exc)) from exc
    await _broadcast_system(
        roomId,
        f"{user['userName']} left the room.",
        "room.members",
        {"members": room["members"]},
    )
    return MemberActionResponse(roomId=roomId, userId=user["userId"], status="left")


@router.delete("/rooms/{roomId}/members/{userId}", response_model=MemberActionResponse)
async def kick(roomId: str, userId: str, user: dict = Depends(get_current_user)):
    require_room_member(roomId, user, leader_only=True)
    try:
        room = remove_member(roomId, userId)
    except ValueError as exc:
        raise AppError(409, "MEMBER_REMOVE_FAILED", str(exc)) from exc
    await _broadcast_system(
        roomId,
        "A member was removed from the room.",
        "room.members",
        {"members": room["members"], "removedUserId": userId},
    )
    return MemberActionResponse(roomId=roomId, userId=userId, status="removed")


@router.patch("/rooms/{roomId}/leader", response_model=RoomStatusResponse)
async def change_leader(
    roomId: str,
    req: TransferLeaderRequest,
    user: dict = Depends(get_current_user),
):
    require_room_member(roomId, user, leader_only=True)
    try:
        room = transfer_leader(roomId, req.userId)
    except ValueError as exc:
        raise AppError(409, "LEADER_TRANSFER_FAILED", str(exc)) from exc
    await _broadcast_system(
        roomId,
        "Room leadership was transferred.",
        "room.leader",
        {"leaderId": room["leaderId"]},
    )
    return RoomStatusResponse(**room)


@router.post("/rooms/{roomId}/current-spot", response_model=UpdateSpotResponse)
async def update_spot(roomId: str, req: UpdateSpotRequest, user: dict = Depends(get_current_user)):
    room = require_room_member(roomId, user, leader_only=True)
    if room["status"] != "active":
        raise AppError(409, "ROOM_NOT_ACTIVE", "Only active rooms can change spots")
    room = update_current_spot(roomId, req.spotId)
    record_event("update_spot", payload={"roomId": roomId, "spotId": req.spotId})
    await room_connections.broadcast(
        roomId, {"type": "room.spot", "data": {"currentSpot": room["currentSpot"]}}
    )
    return UpdateSpotResponse(roomId=roomId, currentSpot=room["currentSpot"], status="updated")


@router.get("/rooms/{roomId}/avatar-state", response_model=AvatarStateResponse)
async def avatar_state(roomId: str, user: dict = Depends(get_current_user)):
    require_room_member(roomId, user)
    return AvatarStateResponse(**get_avatar_state(roomId))


@router.patch("/rooms/{roomId}/status", response_model=UpdateRoomStatusResponse)
async def change_room_status(
    roomId: str,
    req: UpdateRoomStatusRequest,
    user: dict = Depends(get_current_user),
):
    current = require_room_member(roomId, user, leader_only=True)
    if current["status"] == "ended" and req.status != "ended":
        raise AppError(409, "ROOM_ENDED", "An ended room cannot be reopened")
    room = update_room_status(roomId, req.status)
    await _broadcast_system(
        roomId,
        f"Room status changed to {room['status']}.",
        "room.status",
        {"status": room["status"]},
    )
    return UpdateRoomStatusResponse(roomId=roomId, status=room["status"])
