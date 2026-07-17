import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile, WebSocket, WebSocketDisconnect

from app.core.auth import get_current_user, require_room_member
from app.core.config import settings
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.schemas.messages import (
    ChatMediaUploadResponse,
    ConversationListResponse,
    DirectMessageCreateRequest,
    DirectMessageListResponse,
    DirectMessageResponse,
    MessageCreateRequest,
    MessageListResponse,
    RoomMessageResponse,
)
from app.services.messages import (
    create_direct_message,
    create_message,
    list_conversations,
    list_direct_messages,
    list_messages,
    mark_conversation_read,
)
from app.services.realtime import room_connections
from app.services.users import consume_ws_ticket

router = APIRouter()

CHAT_UPLOAD_DIR = Path("uploads") / "chat"
_IMAGE_TYPES = {".jpg": {"image/jpeg"}, ".jpeg": {"image/jpeg"}, ".png": {"image/png"}, ".webp": {"image/webp"}}
_AUDIO_TYPES = {
    ".wav": {"audio/wav", "audio/x-wav"},
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".webm": {"audio/webm", "video/webm"},
    ".ogg": {"audio/ogg", "application/ogg"},
    ".m4a": {"audio/mp4", "audio/x-m4a"},
}


def _valid_signature(suffix: str, header: bytes, kind: str) -> bool:
    if kind == "image":
        return {
            ".jpg": header.startswith(b"\xff\xd8\xff"),
            ".jpeg": header.startswith(b"\xff\xd8\xff"),
            ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
            ".webp": header[:4] == b"RIFF" and header[8:12] == b"WEBP",
        }.get(suffix, False)
    return {
        ".wav": header.startswith(b"RIFF") and header[8:12] == b"WAVE",
        ".mp3": header.startswith(b"ID3") or header[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"},
        ".webm": header.startswith(b"\x1a\x45\xdf\xa3"),
        ".ogg": header.startswith(b"OggS"),
        ".m4a": b"ftyp" in header[:16],
    }.get(suffix, False)


def _require_peer(room: dict, user_id: str, peer_user_id: str) -> None:
    if peer_user_id == user_id:
        raise AppError(422, "INVALID_DIRECT_RECIPIENT", "Cannot send a direct message to yourself")
    if not any(member["userId"] == peer_user_id for member in room.get("members", [])):
        raise AppError(404, "ROOM_MEMBER_NOT_FOUND", "Direct-message recipient is not in this room")


@router.get("/api/rooms/{roomId}/messages", response_model=MessageListResponse)
async def get_messages(
    roomId: str,
    limit: int = Query(default=100, ge=1, le=200),
    cursor: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    require_room_member(roomId, user)
    messages, next_cursor = list_messages(roomId, limit=limit, cursor=cursor)
    mark_conversation_read(roomId, user["userId"], None)
    return MessageListResponse(messages=messages, nextCursor=next_cursor)


@router.post("/api/rooms/{roomId}/messages", response_model=RoomMessageResponse)
async def post_message(
    roomId: str,
    req: MessageCreateRequest,
    user: dict = Depends(get_current_user),
):
    enforce_rate_limit("messages", user["userId"], 60, 60)
    room = require_room_member(roomId, user, leader_only=req.type == "broadcast")
    if room["status"] == "ended":
        raise AppError(409, "ROOM_ENDED", "Ended rooms are read-only")
    message = create_message(
        room_id=room["roomId"],
        user_id=user["userId"],
        user_name=user["userName"],
        content=req.content,
        message_type=req.type,
        kind=req.kind,
        media_url=req.mediaUrl,
        file_name=req.fileName,
        duration=req.duration,
    )
    await room_connections.broadcast(roomId, {"type": "room.message", "data": message})
    await room_connections.broadcast(roomId, {"type": "conversation.updated", "data": {"conversationId": "group"}})
    return RoomMessageResponse(**message)


@router.get("/api/rooms/{roomId}/conversations", response_model=ConversationListResponse)
async def get_conversations(roomId: str, user: dict = Depends(get_current_user)):
    room = require_room_member(roomId, user)
    return ConversationListResponse(conversations=list_conversations(room, user["userId"]))


@router.get("/api/rooms/{roomId}/direct/{peerUserId}/messages", response_model=DirectMessageListResponse)
async def get_direct_messages(
    roomId: str,
    peerUserId: str,
    limit: int = Query(default=100, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    room = require_room_member(roomId, user)
    _require_peer(room, user["userId"], peerUserId)
    messages = list_direct_messages(roomId, user["userId"], peerUserId, limit)
    mark_conversation_read(roomId, user["userId"], peerUserId)
    return DirectMessageListResponse(messages=messages)


@router.post("/api/rooms/{roomId}/direct/{peerUserId}/messages", response_model=DirectMessageResponse)
async def post_direct_message(
    roomId: str,
    peerUserId: str,
    req: DirectMessageCreateRequest,
    user: dict = Depends(get_current_user),
):
    enforce_rate_limit("messages", user["userId"], 60, 60)
    room = require_room_member(roomId, user)
    _require_peer(room, user["userId"], peerUserId)
    if room["status"] == "ended":
        raise AppError(409, "ROOM_ENDED", "Ended rooms are read-only")
    message = create_direct_message(
        roomId,
        user["userId"],
        peerUserId,
        user["userName"],
        req.content,
        kind=req.kind,
        media_url=req.mediaUrl,
        file_name=req.fileName,
        duration=req.duration,
    )
    event = {"type": "direct.message", "data": message}
    await room_connections.send_to_user(roomId, user["userId"], event)
    await room_connections.send_to_user(roomId, peerUserId, event)
    update = {"type": "conversation.updated", "data": {"conversationId": "direct:" + user["userId"], "peerUserId": user["userId"]}}
    await room_connections.send_to_user(roomId, peerUserId, update)
    await room_connections.send_to_user(roomId, user["userId"], {"type": "conversation.updated", "data": {"conversationId": "direct:" + peerUserId, "peerUserId": peerUserId}})
    return DirectMessageResponse(**message)


@router.post("/api/rooms/{roomId}/chat-media", response_model=ChatMediaUploadResponse)
async def upload_chat_media(
    roomId: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    require_room_member(roomId, user)
    enforce_rate_limit("chat_media", user["userId"], 20, 600)
    suffix = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()
    if suffix in _IMAGE_TYPES and content_type in _IMAGE_TYPES[suffix]:
        kind, maximum = "image", 10 * 1024 * 1024
    elif suffix in _AUDIO_TYPES and content_type in _AUDIO_TYPES[suffix]:
        kind, maximum = "audio", settings.max_audio_upload_bytes
    else:
        raise AppError(415, "UNSUPPORTED_CHAT_MEDIA", "Only JPG, PNG, WebP and supported audio files can be sent")
    CHAT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    final_name = f"chat_{uuid4().hex}{suffix}"
    final_path = CHAT_UPLOAD_DIR / final_name
    temp_path = final_path.with_suffix(final_path.suffix + ".part")
    total, header = 0, b""
    try:
        with temp_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                if not header:
                    header = chunk[:32]
                total += len(chunk)
                if total > maximum:
                    raise AppError(413, "CHAT_MEDIA_TOO_LARGE", "Chat media file is too large")
                output.write(chunk)
        if not _valid_signature(suffix, header, kind):
            raise AppError(415, "INVALID_CHAT_MEDIA", "Uploaded file content does not match its extension")
        temp_path.replace(final_path)
    finally:
        temp_path.unlink(missing_ok=True)
        await file.close()
    return ChatMediaUploadResponse(
        mediaUrl=f"/uploads/chat/{final_name}", kind=kind, fileName=(file.filename or final_name)[:255]
    )


@router.websocket("/ws/rooms/{roomId}")
async def room_websocket(websocket: WebSocket, roomId: str, ticket: str = Query(default="")):
    user = consume_ws_ticket(ticket, roomId) if ticket else None
    if user is None:
        await websocket.close(code=4401)
        return
    try:
        room = require_room_member(roomId, user)
    except AppError as exc:
        await websocket.close(code=4404 if exc.status_code == 404 else 4403)
        return

    await room_connections.connect(roomId, websocket, user["userId"])
    await websocket.send_json(
        {
            "type": "room.connected",
            "data": {
                "roomId": roomId,
                "userId": user["userId"],
                "connections": room_connections.connection_count(roomId),
                "messages": list_messages(roomId, limit=100)[0],
            },
        }
    )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": {"detail": "Invalid JSON"}})
                continue

            event_type = payload.get("type")
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if event_type != "message":
                await websocket.send_json({"type": "error", "data": {"detail": "Unsupported event type"}})
                continue

            room = require_room_member(roomId, user)
            if room["status"] == "ended":
                await websocket.send_json({"type": "error", "data": {"detail": "Ended rooms are read-only"}})
                continue
            try:
                enforce_rate_limit("messages", user["userId"], 60, 60)
            except AppError as exc:
                await websocket.send_json({"type": "error", "data": {"detail": exc.detail, "errorCode": exc.error_code}})
                continue

            message_type = payload.get("messageType", "user")
            if message_type not in {"user", "broadcast"}:
                await websocket.send_json({"type": "error", "data": {"detail": "Invalid message type"}})
                continue
            if message_type == "broadcast" and room["leaderId"] != user["userId"] and user.get("role") != "admin":
                await websocket.send_json({"type": "error", "data": {"detail": "Only the room leader can broadcast"}})
                continue

            try:
                message = create_message(
                    room_id=roomId,
                    user_id=user["userId"],
                    user_name=user["userName"],
                    content=str(payload.get("content", "")),
                    message_type=message_type,
                    kind=str(payload.get("kind", "text")),
                    media_url=str(payload.get("mediaUrl", "")),
                    file_name=str(payload.get("fileName", "")),
                    duration=float(payload.get("duration", 0) or 0),
                )
            except ValueError as exc:
                await websocket.send_json({"type": "error", "data": {"detail": str(exc)}})
                continue
            await room_connections.broadcast(roomId, {"type": "room.message", "data": message})
            await room_connections.broadcast(roomId, {"type": "conversation.updated", "data": {"conversationId": "group"}})
    except WebSocketDisconnect:
        room_connections.disconnect(roomId, websocket)
    except Exception:
        room_connections.disconnect(roomId, websocket)
        await websocket.close(code=1011)
