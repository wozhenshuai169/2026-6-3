import base64
import json
from time import time_ns
from uuid import uuid4

from app.core.database import database

MESSAGE_TYPES = {"user", "ai", "system", "broadcast"}


def create_message(
    room_id: str,
    user_id: str | None,
    user_name: str,
    content: str,
    message_type: str = "user",
) -> dict:
    clean_content = content.strip()
    if not clean_content:
        raise ValueError("Message content cannot be empty")
    if len(clean_content) > 1000:
        raise ValueError("Message content is too long")
    if message_type not in MESSAGE_TYPES:
        raise ValueError("Invalid message type")

    message = {
        "id": uuid4().hex,
        "roomId": room_id,
        "userId": user_id or "system",
        "userName": user_name,
        "content": clean_content,
        "type": message_type,
        "timestamp": time_ns() // 1_000_000,
    }
    with database() as connection:
        connection.execute(
            """
            INSERT INTO room_messages (
                message_id, room_id, user_id, user_name, content, message_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message["id"],
                room_id,
                user_id,
                user_name,
                clean_content,
                message_type,
                message["timestamp"],
            ),
        )
    return message


def list_messages(
    room_id: str,
    limit: int = 100,
    cursor: str | None = None,
) -> tuple[list[dict], str | None]:
    bounded_limit = max(1, min(limit, 200))
    query = """
        SELECT message_id, room_id, user_id, user_name, content, message_type, created_at
        FROM room_messages
        WHERE room_id = ?
    """
    params: list = [room_id]
    if cursor:
        try:
            decoded = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8"))
            before_time, before_id = int(decoded[0]), str(decoded[1])
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid message cursor") from exc
        query += " AND (created_at < ? OR (created_at = ? AND message_id < ?))"
        params.extend([before_time, before_time, before_id])
    query += " ORDER BY created_at DESC, message_id DESC LIMIT ?"
    params.append(bounded_limit)

    with database() as connection:
        rows = connection.execute(query, params).fetchall()

    messages = [
        {
            "id": row["message_id"],
            "roomId": row["room_id"],
            "userId": row["user_id"] or "system",
            "userName": row["user_name"],
            "content": row["content"],
            "type": row["message_type"],
            "timestamp": row["created_at"],
        }
        for row in reversed(rows)
    ]
    next_cursor = None
    if len(rows) == bounded_limit:
        oldest = rows[-1]
        payload = json.dumps([oldest["created_at"], oldest["message_id"]]).encode("utf-8")
        next_cursor = base64.urlsafe_b64encode(payload).decode("ascii")
    return messages, next_cursor
