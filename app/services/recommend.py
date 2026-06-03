"""路线推荐服务 —— 通过 Map Provider 规划游览路线。"""

from app.services.rooms import get_room
from app.providers.factory import get_map


async def recommend_route(room_id: str, user_id: str, preferences: dict | None = None) -> dict | None:
    """路线推荐：调用 Map Provider 返回最佳路线。"""
    room = get_room(room_id)
    if room is None:
        return None

    # 从房间获取当前景点列表
    current_spot = room.get("currentSpot", "")
    spot_ids = [current_spot] if current_spot else []

    prefs = preferences or {}

    provider = get_map()
    result = await provider.plan_route(spot_ids, prefs)

    return {
        "routeName": result.route_name,
        "estimatedTime": result.estimated_time,
        "spots": result.spots,
        "reason": result.reason,
        "distance": result.distance,
        "difficulty": result.difficulty,
        "matchedPreferences": result.matched_preferences,
        "scoreBreakdown": result.score_breakdown,
    }
