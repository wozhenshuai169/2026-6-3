from uuid import uuid4

from app.services.users import get_user_by_token

rooms: dict[str, dict] = {}


def create_room(leader_id: str) -> dict:
    room_id = str(uuid4())
    rooms[room_id] = {
        "roomId": room_id,
        "leaderId": leader_id,
        "members": [],
        "currentSpot": "",
        "status": "active",
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
