from app.services.rooms import get_room


def recommend_route(room_id: str, user_id: str, preferences: dict | None = None) -> dict | None:
    """Mock 路线推荐：根据偏好返回不同的游览路线"""
    room = get_room(room_id)
    if room is None:
        return None

    prefs = preferences or {}
    interest = prefs.get("interest", [])
    with_elderly = prefs.get("withElderly", False)
    with_children = prefs.get("withChildren", False)
    physical = prefs.get("physicalStrength", "medium")
    avoid_crowd = prefs.get("avoidCrowd", False)
    time_limit = prefs.get("timeLimit", 60)

    # 有老人/体力弱/避拥挤 → 轻松线
    if with_elderly or physical == "low" or avoid_crowd:
        return {
            "routeName": "历史轻松线",
            "estimatedTime": 55,
            "spots": [
                {"spotId": "spot_001", "spotName": "入口广场", "stayMinutes": 5},
                {"spotId": "spot_002", "spotName": "主展厅", "stayMinutes": 20},
                {"spotId": "spot_005", "spotName": "休息区", "stayMinutes": 10},
                {"spotId": "spot_006", "spotName": "东门出口", "stayMinutes": 5},
            ],
            "reason": "该路线步行距离较短，包含休息点，适合有老人同行的游客。",
        }

    # 历史/摄影兴趣 → 深读线
    if "历史" in interest or "摄影" in interest:
        return {
            "routeName": "历史深读线",
            "estimatedTime": 80,
            "spots": [
                {"spotId": "spot_001", "spotName": "入口广场", "stayMinutes": 5},
                {"spotId": "spot_002", "spotName": "主展厅", "stayMinutes": 25},
                {"spotId": "spot_003", "spotName": "钟楼", "stayMinutes": 15},
                {"spotId": "spot_004", "spotName": "鼓楼", "stayMinutes": 15},
                {"spotId": "spot_007", "spotName": "石刻长廊", "stayMinutes": 20},
            ],
            "reason": "覆盖历史和建筑讲解点，匹配深度探索偏好，适合有摄影兴趣的游客。",
        }

    # 带孩子 → 亲子线
    if with_children:
        return {
            "routeName": "亲子探索线",
            "estimatedTime": 45,
            "spots": [
                {"spotId": "spot_001", "spotName": "入口广场", "stayMinutes": 5},
                {"spotId": "spot_008", "spotName": "互动体验区", "stayMinutes": 20},
                {"spotId": "spot_005", "spotName": "休息区", "stayMinutes": 10},
                {"spotId": "spot_002", "spotName": "主展厅", "stayMinutes": 10},
            ],
            "reason": "路线节奏轻松，包含互动体验环节，适合带孩子的家庭游客。",
        }

    # 默认：经典线
    return {
        "routeName": "经典中轴线",
        "estimatedTime": 60,
        "spots": [
            {"spotId": "spot_001", "spotName": "入口广场", "stayMinutes": 10},
            {"spotId": "spot_002", "spotName": "主展厅", "stayMinutes": 20},
            {"spotId": "spot_003", "spotName": "钟楼", "stayMinutes": 15},
            {"spotId": "spot_004", "spotName": "鼓楼", "stayMinutes": 15},
        ],
        "reason": "经典中轴游览路线，覆盖景区核心景点，时间适中。",
    }
