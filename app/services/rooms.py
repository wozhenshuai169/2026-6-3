from uuid import uuid4

from app.services.users import get_user_by_token

rooms: dict[str, dict] = {}


def create_room(
    leader: dict,
    room_name: str,
    scenic_area_id: str,
    route_id: str,
) -> dict:
    room_id = str(uuid4())
    rooms[room_id] = {
        "roomId": room_id,
        "leaderId": leader["userId"],
        "roomName": room_name,
        "scenicAreaId": scenic_area_id,
        "routeId": route_id,
        "members": [{"userId": leader["userId"], "userName": leader["userName"]}],
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
            "text": "The tour is paused.",
            "audioUrl": "",
        }
    if member_count == 0:
        return {
            "aiStatus": "idle",
            "emotion": "neutral",
            "action": "idle",
            "text": "Waiting for visitors to join the room.",
            "audioUrl": "",
        }
    if current_spot:
        return {
            "aiStatus": "speaking",
            "emotion": "friendly",
            "action": "speaking",
            "text": f"Welcome to {current_spot}. Let me introduce its history and culture.",
            "audioUrl": "",
        }
    return {
        "aiStatus": "idle",
        "emotion": "friendly",
        "action": "idle",
        "text": "Hello, I am your intelligent tour guide.",
        "audioUrl": "",
    }
