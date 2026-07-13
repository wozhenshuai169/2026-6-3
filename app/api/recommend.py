from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.schemas.recommend import RouteRecommendRequest, RouteRecommendResponse
from app.services.recommend import recommend_route

router = APIRouter(prefix="/api/recommend")


@router.post("/route", response_model=RouteRecommendResponse)
async def route_recommend(req: RouteRecommendRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    enforce_rate_limit("recommend", user["userId"], 20, 60)
    result = await recommend_route(
        req.roomId, user["userId"],
        req.preferences.model_dump() if req.preferences else None,
    )
    if result is None:
        raise AppError(404, "ROOM_NOT_FOUND", "Room not found")
    return RouteRecommendResponse(**result)
