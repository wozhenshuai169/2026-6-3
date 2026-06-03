from app.services.rooms import get_room


# Mock 图片识景结果集
_MOCK_SPOTS = {
    "spot_001": {
        "spotId": "spot_001",
        "spotName": "入口广场",
        "description": "你拍到的入口广场，是景区的门户，始建于清代，两侧有石狮守护。",
        "related": [
            {"spotId": "spot_002", "spotName": "主展厅"},
            {"spotId": "spot_003", "spotName": "钟楼"},
        ],
    },
    "spot_002": {
        "spotId": "spot_002",
        "spotName": "主展厅",
        "description": "你拍到的是主展厅，它是景区内保存最完整的传统建筑之一，内部陈列了大量珍贵文物。",
        "related": [
            {"spotId": "spot_001", "spotName": "入口广场"},
            {"spotId": "spot_004", "spotName": "鼓楼"},
        ],
    },
    "spot_003": {
        "spotId": "spot_003",
        "spotName": "钟楼",
        "description": "你拍到的是钟楼，它是景区内保存较完整的传统建筑之一，高约15米，每逢整点仍会敲响。",
        "related": [
            {"spotId": "spot_004", "spotName": "鼓楼"},
        ],
    },
}


def recognize_image(room_id: str, user_id: str, image_url: str, current_spot_id: str = "") -> dict | None:
    """Mock 图片识景：根据当前景点或默认返回识别结果"""
    room = get_room(room_id)
    if room is None:
        return None

    spot_id = current_spot_id or room.get("currentSpot", "")

    if spot_id and spot_id in _MOCK_SPOTS:
        spot = _MOCK_SPOTS[spot_id]
    else:
        # 默认返回钟楼
        spot = _MOCK_SPOTS["spot_003"]

    return {
        "recognizedSpot": {
            "spotId": spot["spotId"],
            "spotName": spot["spotName"],
            "confidence": 0.87,
        },
        "description": spot["description"],
        "relatedSpots": spot["related"],
    }
