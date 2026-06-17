import json
from pathlib import Path
from time import time
from uuid import uuid4

from app.services.users import get_user_by_token

rooms: dict[str, dict] = {}
DATA_DIR = Path("data")


def _load_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _route_spots(route_id: str) -> list[str]:
    for route in _load_json("routes.json"):
        if route.get("routeId") == route_id:
            return list(route.get("spotIds", []))
    return []


def spot_exists(spot_id: str) -> bool:
    if not spot_id:
        return False
    for spot in _load_json("vision_spots.json"):
        if spot.get("spotId") == spot_id:
            return True
    for node in _load_json("path_nodes.json"):
        if node.get("spotId") == spot_id:
            return True
    for route in _load_json("routes.json"):
        if spot_id in route.get("spotIds", []):
            return True
    return False


def create_room(
    leader_id: str,
    room_name: str = "",
    scenic_area_id: str = "",
    route_id: str = "",
) -> dict:
    room_id = str(uuid4())
    rooms[room_id] = {
        "roomId": room_id,
        "leaderId": leader_id,
        "roomName": room_name,
        "scenicAreaId": scenic_area_id,
        "routeId": route_id,
        "routeSpotIds": _route_spots(route_id),
        "members": [],
        "currentSpot": "",
        "status": "active",
        "voiceLogs": [],
        "visionLogs": [],
        "recommendationLogs": [],
    }
    return rooms[room_id]


def get_room(room_id: str) -> dict | None:
    return rooms.get(room_id)


def join_room(room_id: str, token: str) -> tuple[dict | None, str | None, str | None]:
    room = rooms.get(room_id)
    if room is None:
        return None, None, None
    user = get_user_by_token(token)
    if user is None:
        return room, None, None
    if not any(member["userId"] == user["userId"] for member in room["members"]):
        room["members"].append({"userId": user["userId"], "userName": user["userName"]})
    return room, user["userId"], user["userName"]


def update_current_spot(room_id: str, spot_id: str) -> dict | None:
    room = rooms.get(room_id)
    if room is None:
        return None
    room["currentSpot"] = spot_id
    return room


def add_spot_to_route(
    room_id: str,
    spot_id: str,
    position: str = "append",
    source: str | None = None,
) -> dict | None:
    room = rooms.get(room_id)
    if room is None:
        return None

    route_spots = room.setdefault("routeSpotIds", [])
    if spot_id in route_spots:
        status = "already_exists"
    elif position == "afterCurrent" and room.get("currentSpot") in route_spots:
        index = route_spots.index(room["currentSpot"]) + 1
        route_spots.insert(index, spot_id)
        status = "added"
    else:
        route_spots.append(spot_id)
        status = "added"

    room.setdefault("routeEvents", []).append(
        {
            "spotId": spot_id,
            "position": position,
            "source": source or "manual",
            "status": status,
            "timestamp": time(),
        }
    )
    return {"room": room, "status": status}


def _append_log(room_id: str, key: str, payload: dict) -> dict | None:
    room = rooms.get(room_id)
    if room is None:
        return None
    item = {"timestamp": time(), **payload}
    room.setdefault(key, []).append(item)
    return item


def record_voice_log(room_id: str, payload: dict) -> dict | None:
    return _append_log(room_id, "voiceLogs", payload)


def record_vision_log(room_id: str, payload: dict) -> dict | None:
    return _append_log(room_id, "visionLogs", payload)


def record_recommendation_log(room_id: str, payload: dict) -> dict | None:
    return _append_log(room_id, "recommendationLogs", payload)


def get_room_logs(room_id: str, key: str, limit: int = 50) -> list[dict] | None:
    room = rooms.get(room_id)
    if room is None:
        return None
    bounded_limit = max(1, min(limit, 200))
    return list(reversed(room.get(key, [])[-bounded_limit:]))


def get_avatar_state(room_id: str) -> dict | None:
    room = rooms.get(room_id)
    if room is None:
        return None

    status = room.get("status", "active")
    current_spot = room.get("currentSpot", "")
    member_count = len(room.get("members", []))

    if status != "active":
        return {
            "aiStatus": "paused",
            "emotion": "neutral",
            "action": "paused",
            "text": "导览已暂停。",
            "audioUrl": "",
        }
    if member_count == 0:
        return {
            "aiStatus": "idle",
            "emotion": "neutral",
            "action": "idle",
            "text": "等待游客加入房间。",
            "audioUrl": "",
        }
    if current_spot:
        return {
            "aiStatus": "speaking",
            "emotion": "friendly",
            "action": "speaking",
            "text": f"欢迎来到{current_spot}，让我为大家介绍这里的历史和文化。",
            "audioUrl": "",
        }
    return {
        "aiStatus": "idle",
        "emotion": "friendly",
        "action": "idle",
        "text": "大家好，我是您的智能导游，随时为您解答问题。",
        "audioUrl": "",
    }
