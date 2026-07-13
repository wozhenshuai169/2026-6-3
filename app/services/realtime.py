from fastapi import WebSocket


class RoomConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(room_id, set()).add(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(room_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(room_id, None)

    async def broadcast(self, room_id: str, event: dict) -> None:
        connections = list(self._connections.get(room_id, set()))
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(event)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(room_id, websocket)

    def connection_count(self, room_id: str) -> int:
        return len(self._connections.get(room_id, set()))


room_connections = RoomConnectionManager()
