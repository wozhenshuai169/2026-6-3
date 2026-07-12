from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user, require_matching_user, require_room_member
from app.schemas.recommend import RouteRecommendRequest, RouteRecommendResponse
from app.services.recommend import recommend_route

router = APIRouter(prefix="/api/recommend")


@router.post("/route", response_model=RouteRecommendResponse)
async def route_recommend(req: RouteRecommendRequest, user: dict = Depends(get_current_user)):
    require_matching_user(req.userId, user)
    require_room_member(req.roomId, user)
    result = await recommend_route(
        req.roomId, user["userId"],
        req.preferences.model_dump() if req.preferences else None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RouteRecommendResponse(**result)
