from fastapi import APIRouter

from app.services.scenic_map import (
    get_current_scenic_context,
    get_scenic_area,
    list_route_templates,
)


router = APIRouter(prefix="/api/map")


@router.get("/scenic-areas/current")
async def current_scenic_area():
    """返回高德实时主景区、独立关联景区和真实 POI。"""

    return await get_current_scenic_context()


@router.get("/scenic-areas/{scenic_area_id}/routes")
async def scenic_area_routes(scenic_area_id: str):
    area = get_scenic_area(scenic_area_id)
    return {
        "scenicAreaId": area["scenicAreaId"],
        "scenicAreaName": area["scenicAreaName"],
        "routes": [
            {
                "routeId": route["routeId"],
                "routeName": route["title"],
                "estimatedTime": route["maxMinutes"],
                "difficulty": route["difficulty"],
                "tags": route.get("tags", []),
                "spotIds": [spot["spotId"] for spot in route.get("spots", [])],
                "spots": route.get("spots", []),
            }
            for route in list_route_templates(scenic_area_id)
        ],
    }
