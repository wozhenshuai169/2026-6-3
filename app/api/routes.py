import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/routes")
DATA_DIR = Path("data")


def _load_routes() -> list[dict]:
    path = DATA_DIR / "routes.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("")
async def list_routes():
    routes = _load_routes()
    return {
        "routes": [
            {
                "routeId": route.get("routeId"),
                "routeName": route.get("title"),
                "estimatedTime": route.get("durationMinutes"),
                "difficulty": route.get("difficulty"),
                "tags": route.get("tags", []),
                "spotIds": route.get("spotIds", []),
            }
            for route in routes
        ]
    }


@router.get("/{route_id}")
async def get_route(route_id: str):
    for route in _load_routes():
        if route.get("routeId") == route_id:
            return {
                "routeId": route.get("routeId"),
                "routeName": route.get("title"),
                "estimatedTime": route.get("durationMinutes"),
                "difficulty": route.get("difficulty"),
                "walkingDifficulty": route.get("walkingDifficulty"),
                "tags": route.get("tags", []),
                "spotIds": route.get("spotIds", []),
                "suitableForChildren": route.get("suitableForChildren", False),
                "suitableForElderly": route.get("suitableForElderly", False),
            }
    raise HTTPException(status_code=404, detail="Route not found")
