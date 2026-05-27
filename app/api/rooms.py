from fastapi import APIRouter, HTTPException

from app.schemas.rooms import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    RoomStatusResponse,
    UpdateSpotRequest,
    UpdateSpotResponse,
)
from app.services.rooms import (
    create_room,
    get_room,
    join_room,
    update_current_spot,
)
from app.services.users import get_user_by_token

router = APIRouter(prefix="/api")


@router.post("/rooms", response_model=CreateRoomResponse)
async def create(req: CreateRoomRequest):
    user = get_user_by_token(req.token)
    if user is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    room = create_room(user["userId"])
    return CreateRoomResponse(roomId=room["roomId"], status="created")


@router.get("/rooms/{roomId}", response_model=RoomStatusResponse)
async def get_status(roomId: str):
    room = get_room(roomId)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
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
        raise HTTPException(status_code=404, detail="房间不存在")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return JoinRoomResponse(roomId=roomId, userId=user_id, status="joined")


@router.post("/rooms/{roomId}/current-spot", response_model=UpdateSpotResponse)
async def update_spot(roomId: str, req: UpdateSpotRequest):
    room = update_current_spot(roomId, req.spotId)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return UpdateSpotResponse(
        roomId=roomId,
        currentSpot=req.spotId,
        status="updated",
    )
