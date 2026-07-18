"""RouteRecommender — 路线推荐（Mock）。"""


def recommend(roomId: str, currentSpot: str = "", preferences: list = None, context: dict = None) -> dict:
    _ = (roomId, preferences, context)
    return {
        "recommendedRouteId": "route_002",
        "reason": f"当前在 {currentSpot or '起点'}，推荐前往人气最高的下一个景点。",
        "alternatives": [
            {"routeId": "route_001", "name": "经典路线", "duration": "2小时"},
            {"routeId": "route_003", "name": "深度探索路线", "duration": "3.5小时"},
        ],
        "stateUpdate": {},
    }
