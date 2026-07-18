"""Route recommendation service."""

from time import perf_counter

from app.services.algorithm_facade import algorithm_facade
from app.services.rooms import get_room
from app.services.scenic_map import recommend_scenic_route
from app.services.users import get_user_memory_tags
from app.services.stats import record_event


async def recommend_route(
    room_id: str,
    user_id: str,
    preferences: dict | None = None,
    scenic_area_id: str | None = None,
) -> dict | None:
    started = perf_counter()
    try:
        if scenic_area_id:
            response = await recommend_scenic_route(scenic_area_id, preferences or {})
            record_event(
                "route_recommend",
                success=True,
                latency_ms=(perf_counter() - started) * 1000,
                payload={
                    "roomId": room_id,
                    "routeId": response["routeId"],
                    "currentSpot": "",
                    "algorithm": "amap_real_route",
                },
            )
            return response

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
        response = algorithm_facade.recommend(
            room,
            user_id,
            preferences,
            get_user_memory_tags(user_id),
        )
        record_event(
            "route_recommend",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": room_id,
                "routeId": response["routeId"],
                "currentSpot": current_spot,
                "algorithm": "unified_legacy",
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
