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
