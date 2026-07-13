import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.core.auth import get_current_user, require_room_member
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.schemas.messages import MessageCreateRequest, MessageListResponse, RoomMessageResponse
from app.services.messages import create_message, list_messages
from app.services.realtime import room_connections
from app.services.users import consume_ws_ticket

router = APIRouter()


@router.get("/api/rooms/{roomId}/messages", response_model=MessageListResponse)
async def get_messages(
    roomId: str,
    limit: int = Query(default=100, ge=1, le=200),
    cursor: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    require_room_member(roomId, user)
    messages, next_cursor = list_messages(roomId, limit=limit, cursor=cursor)
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
    )
    await room_connections.broadcast(roomId, {"type": "room.message", "data": message})
    return RoomMessageResponse(**message)


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
                )
            except ValueError as exc:
                await websocket.send_json({"type": "error", "data": {"detail": str(exc)}})
                continue
            await room_connections.broadcast(roomId, {"type": "room.message", "data": message})
    except WebSocketDisconnect:
        room_connections.disconnect(roomId, websocket)
    except Exception:
        room_connections.disconnect(roomId, websocket)
        await websocket.close(code=1011)
