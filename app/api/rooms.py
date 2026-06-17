from fastapi import APIRouter, HTTPException

from app.schemas.avatar import AvatarStateResponse
from app.schemas.rooms import (
    AddSpotRequest,
    AddSpotResponse,
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    RoomLogListResponse,
    RoomStatusResponse,
    UpdateSpotRequest,
    UpdateSpotResponse,
)
from app.services.rooms import (
    add_spot_to_route,
    create_room,
    get_avatar_state,
    get_room,
    get_room_logs,
    join_room,
    spot_exists,
    update_current_spot,
)
from app.services.stats import record_event
from app.services.users import get_user_by_token

router = APIRouter(prefix="/api")


@router.post("/rooms", response_model=CreateRoomResponse)
async def create(req: CreateRoomRequest):
    user = get_user_by_token(req.token)
    if user is None:
        record_event("create_room", success=False, payload={"error": "invalid_token"})
        raise HTTPException(status_code=401, detail="Invalid token")
    room = create_room(user["userId"], req.roomName, req.scenicAreaId, req.routeId)
    record_event("create_room", success=True, payload={"roomId": room["roomId"], "leaderId": user["userId"]})
    return CreateRoomResponse(roomId=room["roomId"], status="created")


@router.get("/rooms/{roomId}", response_model=RoomStatusResponse)
async def get_status(roomId: str):
    room = get_room(roomId)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomStatusResponse(
        roomId=room["roomId"],
        roomName=room.get("roomName", ""),
        scenicAreaId=room.get("scenicAreaId", ""),
        routeId=room.get("routeId", ""),
        routeSpotIds=room.get("routeSpotIds", []),
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


@router.post("/rooms/{roomId}/add-spot", response_model=AddSpotResponse)
async def add_spot(roomId: str, req: AddSpotRequest):
    if req.position not in {"append", "afterCurrent"}:
        raise HTTPException(status_code=422, detail="position must be append or afterCurrent")
    if not spot_exists(req.spotId):
        raise HTTPException(status_code=404, detail="Spot not found")
    result = add_spot_to_route(roomId, req.spotId, req.position, req.source)
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    room = result["room"]
    record_event(
        "add_route_spot",
        success=True,
        payload={"roomId": roomId, "spotId": req.spotId, "status": result["status"]},
    )
    return AddSpotResponse(
        roomId=roomId,
        routeSpotIds=room.get("routeSpotIds", []),
        addedSpotId=req.spotId,
        status=result["status"],
    )


@router.get("/rooms/{roomId}/avatar-state", response_model=AvatarStateResponse)
async def avatar_state(roomId: str):
    state = get_avatar_state(roomId)
    if state is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return AvatarStateResponse(**state)


@router.get("/rooms/{roomId}/voice-logs", response_model=RoomLogListResponse)
async def voice_logs(roomId: str, limit: int = 50):
    items = get_room_logs(roomId, "voiceLogs", limit)
    if items is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomLogListResponse(roomId=roomId, items=items)


@router.get("/rooms/{roomId}/vision-logs", response_model=RoomLogListResponse)
async def vision_logs(roomId: str, limit: int = 50):
    items = get_room_logs(roomId, "visionLogs", limit)
    if items is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomLogListResponse(roomId=roomId, items=items)


@router.get("/rooms/{roomId}/recommendation-logs", response_model=RoomLogListResponse)
async def recommendation_logs(roomId: str, limit: int = 50):
    items = get_room_logs(roomId, "recommendationLogs", limit)
    if items is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomLogListResponse(roomId=roomId, items=items)
