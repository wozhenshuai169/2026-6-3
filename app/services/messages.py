import base64
import json
from time import time_ns
from uuid import uuid4

from app.core.database import database

MESSAGE_TYPES = {"user", "ai", "system", "broadcast"}
MESSAGE_KINDS = {"text", "image", "audio"}


def _clean_message(
    content: str,
    kind: str,
    media_url: str,
    file_name: str,
    duration: float,
) -> tuple[str, str, str, str, float]:
    clean_content = content.strip()
    clean_kind = kind.strip().lower()
    clean_media_url = media_url.strip()
    clean_file_name = file_name.strip()
    if clean_kind not in MESSAGE_KINDS:
        raise ValueError("Invalid message kind")
    if len(clean_content) > 1000:
        raise ValueError("Message content is too long")
    if clean_kind == "text" and not clean_content:
        raise ValueError("Message content cannot be empty")
    if clean_kind != "text" and not clean_media_url.startswith("/uploads/chat/"):
        raise ValueError("Media message must use an uploaded chat media URL")
    if clean_kind == "text":
        clean_media_url = ""
        clean_file_name = ""
        duration = 0
    return clean_content, clean_kind, clean_media_url, clean_file_name, max(float(duration or 0), 0)


def create_message(
    room_id: str,
    user_id: str | None,
    user_name: str,
    content: str,
    message_type: str = "user",
    *,
    kind: str = "text",
    media_url: str = "",
    file_name: str = "",
    duration: float = 0,
) -> dict:
    if message_type not in MESSAGE_TYPES:
        raise ValueError("Invalid message type")
    clean_content, clean_kind, clean_media_url, clean_file_name, clean_duration = _clean_message(
        content, kind, media_url, file_name, duration
    )

    message = {
        "id": uuid4().hex,
        "roomId": room_id,
        "userId": user_id or "system",
        "userName": user_name,
        "content": clean_content,
        "type": message_type,
        "timestamp": time_ns() // 1_000_000,
        "kind": clean_kind,
        "mediaUrl": clean_media_url,
        "fileName": clean_file_name,
        "duration": clean_duration,
    }
    with database() as connection:
        connection.execute(
            """
            INSERT INTO room_messages (
                message_id, room_id, user_id, user_name, content, message_type, created_at,
                kind, media_url, file_name, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message["id"],
                room_id,
                user_id,
                user_name,
                clean_content,
                message_type,
                message["timestamp"],
                clean_kind,
                clean_media_url,
                clean_file_name,
                clean_duration,
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
        SELECT message_id, room_id, user_id, user_name, content, message_type, created_at,
               kind, media_url, file_name, duration
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
            "kind": row["kind"],
            "mediaUrl": row["media_url"],
            "fileName": row["file_name"],
            "duration": float(row["duration"] or 0),
        }
        for row in reversed(rows)
    ]
    next_cursor = None
    if len(rows) == bounded_limit:
        oldest = rows[-1]
        payload = json.dumps([oldest["created_at"], oldest["message_id"]]).encode("utf-8")
        next_cursor = base64.urlsafe_b64encode(payload).decode("ascii")
    return messages, next_cursor


def _direct_row(row) -> dict:
    return {
        "id": row["message_id"],
        "roomId": row["room_id"],
        "senderId": row["sender_id"],
        "recipientId": row["recipient_id"],
        "senderName": row["sender_name"],
        "content": row["content"],
        "kind": row["kind"],
        "mediaUrl": row["media_url"],
        "fileName": row["file_name"],
        "duration": float(row["duration"] or 0),
        "timestamp": row["created_at"],
    }


def create_direct_message(
    room_id: str,
    sender_id: str,
    recipient_id: str,
    sender_name: str,
    content: str,
    *,
    kind: str = "text",
    media_url: str = "",
    file_name: str = "",
    duration: float = 0,
) -> dict:
    clean_content, clean_kind, clean_media_url, clean_file_name, clean_duration = _clean_message(
        content, kind, media_url, file_name, duration
    )
    message = {
        "id": uuid4().hex,
        "roomId": room_id,
        "senderId": sender_id,
        "recipientId": recipient_id,
        "senderName": sender_name,
        "content": clean_content,
        "kind": clean_kind,
        "mediaUrl": clean_media_url,
        "fileName": clean_file_name,
        "duration": clean_duration,
        "timestamp": time_ns() // 1_000_000,
    }
    with database() as connection:
        connection.execute(
            """
            INSERT INTO direct_messages (
                message_id, room_id, sender_id, recipient_id, sender_name, content,
                kind, media_url, file_name, duration, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message["id"], room_id, sender_id, recipient_id, sender_name,
                clean_content, clean_kind, clean_media_url, clean_file_name,
                clean_duration, message["timestamp"],
            ),
        )
    return message


def _conversation_id(peer_user_id: str | None) -> str:
    return "group" if peer_user_id is None else "direct:" + peer_user_id


def mark_conversation_read(room_id: str, user_id: str, peer_user_id: str | None, read_at: int | None = None) -> None:
    with database() as connection:
        connection.execute(
            """
            INSERT INTO conversation_reads (room_id, user_id, conversation_id, read_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, user_id, conversation_id) DO UPDATE SET read_at = excluded.read_at
            """,
            (room_id, user_id, _conversation_id(peer_user_id), int(read_at or time_ns() // 1_000_000)),
        )


def list_direct_messages(room_id: str, user_id: str, peer_user_id: str, limit: int = 100) -> list[dict]:
    bounded_limit = max(1, min(limit, 200))
    with database() as connection:
        rows = connection.execute(
            """
            SELECT message_id, room_id, sender_id, recipient_id, sender_name, content,
                   kind, media_url, file_name, duration, created_at
            FROM direct_messages
            WHERE room_id = ?
              AND ((sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?))
            ORDER BY created_at DESC, message_id DESC
            LIMIT ?
            """,
            (room_id, user_id, peer_user_id, peer_user_id, user_id, bounded_limit),
        ).fetchall()
    return [_direct_row(row) for row in reversed(rows)]


def list_conversations(room: dict, user_id: str) -> list[dict]:
    room_id = room["roomId"]
    peers = [member for member in room.get("members", []) if member["userId"] != user_id]
    with database() as connection:
        group_latest = connection.execute(
            """
            SELECT content, kind, created_at FROM room_messages
            WHERE room_id = ? ORDER BY created_at DESC, message_id DESC LIMIT 1
            """,
            (room_id,),
        ).fetchone()
        group_read = connection.execute(
            "SELECT read_at FROM conversation_reads WHERE room_id = ? AND user_id = ? AND conversation_id = 'group'",
            (room_id, user_id),
        ).fetchone()
        group_unread = connection.execute(
            "SELECT COUNT(*) AS total FROM room_messages WHERE room_id = ? AND user_id != ? AND created_at > ?",
            (room_id, user_id, int(group_read["read_at"]) if group_read else 0),
        ).fetchone()["total"]
        items = [{
            "conversationId": "group",
            "kind": "group",
            "title": room.get("roomName") or "同行小队",
            "isLeader": False,
            "latestMessage": _preview(group_latest["content"], group_latest["kind"]) if group_latest else "暂无消息",
            "latestAt": int(group_latest["created_at"]) if group_latest else 0,
            "unreadCount": int(group_unread),
        }]
        for peer in peers:
            peer_id = peer["userId"]
            latest = connection.execute(
                """
                SELECT content, kind, created_at FROM direct_messages
                WHERE room_id = ?
                  AND ((sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?))
                ORDER BY created_at DESC, message_id DESC LIMIT 1
                """,
                (room_id, user_id, peer_id, peer_id, user_id),
            ).fetchone()
            read = connection.execute(
                "SELECT read_at FROM conversation_reads WHERE room_id = ? AND user_id = ? AND conversation_id = ?",
                (room_id, user_id, _conversation_id(peer_id)),
            ).fetchone()
            unread = connection.execute(
                """
                SELECT COUNT(*) AS total FROM direct_messages
                WHERE room_id = ? AND sender_id = ? AND recipient_id = ? AND created_at > ?
                """,
                (room_id, peer_id, user_id, int(read["read_at"]) if read else 0),
            ).fetchone()["total"]
            items.append({
                "conversationId": _conversation_id(peer_id),
                "kind": "direct",
                "title": peer["userName"],
                "peerUserId": peer_id,
                "peerUserName": peer["userName"],
                "isLeader": peer_id == room.get("leaderId"),
                "latestMessage": _preview(latest["content"], latest["kind"]) if latest else "开始和他聊聊",
                "latestAt": int(latest["created_at"]) if latest else 0,
                "unreadCount": int(unread),
            })
    return sorted(items, key=lambda item: (item["conversationId"] != "group", -item["latestAt"]))


def _preview(content: str, kind: str) -> str:
    if kind == "image":
        return "[图片]"
    if kind == "audio":
        return "[语音]"
    return content[:80]
