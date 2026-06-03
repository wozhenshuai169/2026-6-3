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
    room["members"].append({"userId": user["userId"], "userName": user["userName"]})
    return room, user["userId"], user["userName"]


def update_current_spot(room_id: str, spot_id: str) -> dict | None:
    room = rooms.get(room_id)
    if room is None:
        return None
    room["currentSpot"] = spot_id
    return room


def get_avatar_state(room_id: str) -> dict | None:
    """根据房间状态推导数字人的 aiStatus / emotion / action"""
    room = rooms.get(room_id)
    if room is None:
        return None

    status = room.get("status", "active")
    current_spot = room.get("currentSpot", "")
    member_count = len(room.get("members", []))

    # 默认状态
    ai_status = "idle"
    emotion = "friendly"
    action = "idle"
    text = "大家好！我是您的智能导游，随时为您解答问题。"
    audio_url = ""

    if status != "active":
        ai_status = "paused"
        emotion = "neutral"
        action = "paused"
        text = "导览已暂停。"
    elif member_count == 0:
        ai_status = "idle"
        emotion = "neutral"
        action = "idle"
        text = "等待游客加入房间..."
    elif current_spot:
        ai_status = "speaking"
        emotion = "friendly"
        action = "speaking"
        text = f"欢迎来到{current_spot}！让我为您介绍这里的历史和文化。"
    else:
        ai_status = "idle"
        emotion = "friendly"
        action = "idle"
        text = "大家好！我是您的智能导游，随时为您解答问题。"

    return {
        "aiStatus": ai_status,
        "emotion": emotion,
        "action": action,
        "text": text,
        "audioUrl": audio_url,
    }
