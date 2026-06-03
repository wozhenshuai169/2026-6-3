from fastapi import APIRouter, HTTPException

from app.schemas.recommend import RouteRecommendRequest, RouteRecommendResponse
from app.services.recommend import recommend_route

router = APIRouter(prefix="/api/recommend")


@router.post("/route", response_model=RouteRecommendResponse)
async def route_recommend(req: RouteRecommendRequest):
    """路线推荐：根据用户偏好推荐游览路线"""
    result = recommend_route(
        req.roomId,
        req.userId,
        req.preferences.model_dump() if req.preferences else None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return RouteRecommendResponse(**result)
