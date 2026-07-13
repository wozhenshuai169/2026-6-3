from time import time
from uuid import uuid4

from app.core.database import database


def _load_members(connection, room_id: str) -> list[dict]:
    rows = connection.execute(
        """
        SELECT u.user_id, u.user_name
        FROM room_members AS rm
        JOIN users AS u ON u.user_id = rm.user_id
        WHERE rm.room_id = ?
        ORDER BY rm.joined_at, u.user_id
        """,
        (room_id,),
    ).fetchall()
    return [{"userId": row["user_id"], "userName": row["user_name"]} for row in rows]


def _row_to_room(connection, row) -> dict | None:
    if row is None:
        return None
    return {
        "roomId": row["room_id"],
        "leaderId": row["leader_id"],
        "roomName": row["room_name"],
        "scenicAreaId": row["scenic_area_id"],
        "routeId": row["route_id"],
        "members": _load_members(connection, row["room_id"]),
        "currentSpot": row["current_spot"],
        "status": row["status"],
    }


def create_room(
    leader: dict,
    room_name: str,
    scenic_area_id: str,
    route_id: str,
) -> dict:
    room_id = str(uuid4())
    now = int(time())
    with database() as connection:
        connection.execute(
            """
            INSERT INTO rooms (
                room_id, leader_id, room_name, scenic_area_id, route_id,
                current_spot, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, '', 'active', ?, ?)
            """,
            (
                room_id,
                leader["userId"],
                room_name.strip(),
                scenic_area_id,
                route_id,
                now,
                now,
            ),
        )
        connection.execute(
            "INSERT INTO room_members (room_id, user_id, joined_at) VALUES (?, ?, ?)",
            (room_id, leader["userId"], now),
        )
    return get_room(room_id)


def get_room(room_id: str) -> dict | None:
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM rooms WHERE room_id = ?",
            (room_id,),
        ).fetchone()
        return _row_to_room(connection, row)


def join_room(room_id: str, user: dict) -> dict | None:
    room = get_room(room_id)
    if room is None:
        return None
    if room["status"] != "active":
        raise ValueError("Room is not accepting new members")

    with database() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO room_members (room_id, user_id, joined_at) VALUES (?, ?, ?)",
            (room_id, user["userId"], int(time())),
        )
    return get_room(room_id)


def leave_room(room_id: str, user_id: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        return None
    if room["leaderId"] == user_id and room["status"] != "ended":
        raise ValueError("The room leader must transfer leadership or end the room before leaving")
    with database() as connection:
        connection.execute(
            "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        )
    return get_room(room_id)


def remove_member(room_id: str, user_id: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        return None
    if room["leaderId"] == user_id:
        raise ValueError("The room leader cannot be removed")
    with database() as connection:
        connection.execute(
            "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        )
    return get_room(room_id)


def transfer_leader(room_id: str, user_id: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        return None
    if not any(member["userId"] == user_id for member in room["members"]):
        raise ValueError("New leader must be a room member")
    with database() as connection:
        connection.execute(
            "UPDATE rooms SET leader_id = ?, updated_at = ? WHERE room_id = ?",
            (user_id, int(time()), room_id),
        )
    return get_room(room_id)


def update_current_spot(room_id: str, spot_id: str) -> dict | None:
    with database() as connection:
        cursor = connection.execute(
            "UPDATE rooms SET current_spot = ?, updated_at = ? WHERE room_id = ?",
            (spot_id.strip(), int(time()), room_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_room(room_id)


def update_room_status(room_id: str, status: str) -> dict | None:
    if status not in {"active", "paused", "ended"}:
        raise ValueError("Invalid room status")
    with database() as connection:
        cursor = connection.execute(
            "UPDATE rooms SET status = ?, updated_at = ? WHERE room_id = ?",
            (status, int(time()), room_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_room(room_id)


def count_rooms(active_only: bool = False) -> int:
    query = "SELECT COUNT(*) AS total FROM rooms"
    params: tuple = ()
    if active_only:
        query += " WHERE status = ?"
        params = ("active",)
    with database() as connection:
        row = connection.execute(query, params).fetchone()
    return int(row["total"])


def get_avatar_state(room_id: str) -> dict | None:
    room = get_room(room_id)
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
