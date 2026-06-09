from fastapi import APIRouter, HTTPException

from app.schemas.recommend import RouteRecommendRequest, RouteRecommendResponse
from app.services.recommend import recommend_route

router = APIRouter(prefix="/api/recommend")


@router.post("/route", response_model=RouteRecommendResponse)
async def route_recommend(req: RouteRecommendRequest):
    result = await recommend_route(
        req.roomId,
        req.userId,
        req.preferences.model_dump() if req.preferences else None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return RouteRecommendResponse(**result)
