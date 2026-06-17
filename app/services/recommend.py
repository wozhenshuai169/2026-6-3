"""Route recommendation service."""

import json
from pathlib import Path
from time import perf_counter

from app.providers.factory import get_map
from app.services.rooms import get_room, record_recommendation_log
from app.services.stats import record_event

DATA_DIR = Path("data")


def _load_routes() -> list[dict]:
    path = DATA_DIR / "routes.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _route_id_for_name(route_name: str) -> str:
    for route in _load_routes():
        if route.get("title") == route_name:
            return route.get("routeId", "")
    return "route_custom"


def _route_for_name(route_name: str) -> dict:
    for route in _load_routes():
        if route.get("title") == route_name:
            return route
    return {}


def _derive_suitable_for(route: dict, preferences: dict | None) -> list[str]:
    explicit = route.get("suitableFor")
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]

    suitable: list[str] = []
    if route.get("suitableForChildren"):
        suitable.append("children")
    if route.get("suitableForElderly"):
        suitable.append("elderly")
    if route.get("walkingDifficulty") == "low" or route.get("difficulty") == "low":
        suitable.append("low physical strength")
    if not suitable:
        suitable.append("general visitors")

    prefs = preferences or {}
    if prefs.get("withChildren") and "children" not in suitable:
        suitable.append("children with guardian")
    if prefs.get("withElderly") and "elderly" not in suitable:
        suitable.append("elderly with companion")
    return suitable


def _derive_notes(route: dict) -> list[str]:
    explicit = route.get("notes") or route.get("cautions")
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]

    notes: list[str] = []
    walking = route.get("walkingDifficulty") or route.get("difficulty")
    if walking == "high":
        notes.append("Long walking distance; plan rest time.")
    elif walking == "medium":
        notes.append("Moderate walking distance; wear comfortable shoes.")
    else:
        notes.append("Low walking load; suitable for a relaxed pace.")
    if not route.get("suitableForElderly", False):
        notes.append("Not the first choice for elderly visitors.")
    return notes


def _normalized_score(score_breakdown: dict) -> float:
    if not score_breakdown:
        return 0.0
    total = sum(float(value) for value in score_breakdown.values())
    max_score = 10.0 if total > 1 else 1.0
    return round(min(total / max_score, 1.0), 2)


async def recommend_route(room_id: str, user_id: str, preferences: dict | None = None) -> dict | None:
    started = perf_counter()
    try:
        room = get_room(room_id)
        if room is None:
            record_event(
                "route_recommend",
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": room_id, "error": "room_not_found"},
            )
            return None

        current_spot = room.get("currentSpot", "")
        spot_ids = [current_spot] if current_spot else []

        provider = get_map()
        result = await provider.plan_route(spot_ids, preferences or {})
        breakdown = {key: float(value) for key, value in result.score_breakdown.items()}
        route_id = _route_id_for_name(result.route_name)
        route_data = _route_for_name(result.route_name)
        response = {
            "routeId": route_id,
            "routeName": result.route_name,
            "score": _normalized_score(breakdown),
            "estimatedTime": result.estimated_time,
            "spots": result.spots,
            "reason": result.reason,
            "distance": result.distance,
            "difficulty": result.difficulty,
            "matchedPreferences": result.matched_preferences,
            "scoreBreakdown": breakdown,
            "suitableFor": _derive_suitable_for(route_data, preferences),
            "notes": _derive_notes(route_data or {"difficulty": result.difficulty}),
        }
        record_event(
            "route_recommend",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "routeId": route_id, "currentSpot": current_spot},
        )
        record_recommendation_log(
            room_id,
            {
                "userId": user_id,
                "routeId": route_id,
                "routeName": result.route_name,
                "score": response["score"],
                "preferences": preferences or {},
                "suitableFor": response["suitableFor"],
                "notes": response["notes"],
            },
        )
        return response
    except Exception as e:
        record_event(
            "route_recommend",
            success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "error": str(e)},
        )
        raise
