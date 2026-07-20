from fastapi import WebSocket


class RoomConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, dict[WebSocket, str]] = {}

    async def connect(self, room_id: str, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(room_id, {})[websocket] = user_id

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(room_id)
        if connections is None:
            return
        connections.pop(websocket, None)
        if not connections:
            self._connections.pop(room_id, None)

    async def broadcast(self, room_id: str, event: dict) -> None:
        connections = list(self._connections.get(room_id, {}))
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(event)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(room_id, websocket)

    async def send_to_user(self, room_id: str, user_id: str, event: dict) -> None:
        """Deliver a sensitive algorithm event only to its intended member."""
        connections = self._connections.get(room_id, {})
        stale: list[WebSocket] = []
        for websocket, connected_user_id in list(connections.items()):
            if connected_user_id != user_id:
                continue
            try:
                await websocket.send_json(event)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(room_id, websocket)

    def connection_count(self, room_id: str) -> int:
        return len(self._connections.get(room_id, {}))


room_connections = RoomConnectionManager()
