import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.knowledge import search_knowledge

router = APIRouter(prefix="/api/spots")
DATA_DIR = Path("data")


def _load_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _spot_map() -> dict[str, dict]:
    spots = {item.get("spotId", ""): item for item in _load_json("vision_spots.json")}
    scenic_data = _load_scenic_areas()
    for area in scenic_data.get("scenicAreas", []):
        for route in area.get("routeTemplates", []):
            route_spots = route.get("spots", [])
            for index, item in enumerate(route_spots):
                spot_id = item.get("spotId", "")
                if not spot_id:
                    continue
                current = spots.setdefault(
                    spot_id,
                    {
                        "spotId": spot_id,
                        "spotName": item.get("name", spot_id),
                        "visualFeatures": [],
                        "relatedSpots": [],
                        "scenicAreaId": area.get("scenicAreaId", ""),
                        "scenicAreaName": area.get("scenicAreaName", ""),
                        "city": area.get("city", ""),
                        "district": area.get("district", ""),
                        "routeNames": [],
                        "stayMinutes": item.get("stayMinutes", 0),
                    },
                )
                current.setdefault("routeNames", [])
                current.setdefault("stayMinutes", item.get("stayMinutes", 0))
                current.setdefault("scenicAreaId", area.get("scenicAreaId", ""))
                current.setdefault("scenicAreaName", area.get("scenicAreaName", ""))
                current.setdefault("city", area.get("city", ""))
                current.setdefault("district", area.get("district", ""))
                current.setdefault("relatedSpots", [])
                route_name = route.get("title", "")
                if route_name and route_name not in current["routeNames"]:
                    current["routeNames"].append(route_name)
                for nearby_index in (index - 1, index + 1):
                    if 0 <= nearby_index < len(route_spots):
                        related = route_spots[nearby_index]
                        related_item = {
                            "spotId": related.get("spotId", ""),
                            "spotName": related.get("name", related.get("spotId", "")),
                        }
                        if related_item not in current["relatedSpots"]:
                            current["relatedSpots"].append(related_item)
    return spots


def _load_scenic_areas() -> dict:
    path = DATA_DIR / "scenic_areas.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _knowledge_chunks(spot_id: str, spot_name: str) -> list[dict]:
    static_chunks = [
        {
            "chunkId": chunk.get("chunkId"),
            "title": chunk.get("title"),
            "topic": chunk.get("topic"),
            "source": chunk.get("source"),
            "content": chunk.get("content"),
        }
        for chunk in _load_json("scenic_chunks.json")
        if chunk.get("spotId") == spot_id
    ][:8]
    if static_chunks:
        return static_chunks
    try:
        results = search_knowledge(spot_name, 8, spot_id=spot_id)
    except ValueError:
        results = []
    return [
        {
            "chunkId": item.get("chunkId"),
            "title": item.get("title"),
            "topic": None,
            "source": item.get("source"),
            "content": item.get("contentPreview"),
        }
        for item in results
    ]


@router.get("/{spot_id}")
async def get_spot(spot_id: str):
    spots = _spot_map()
    spot = spots.get(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    chunks = _knowledge_chunks(spot_id, spot.get("spotName", spot_id))
    description = spot.get("description", "")
    if not description and chunks:
        description = chunks[0].get("content", "")
    if not description and spot.get("scenicAreaName"):
        stay_minutes = int(spot.get("stayMinutes", 0) or 0)
        stay_text = f"，路线建议停留约 {stay_minutes} 分钟" if stay_minutes else ""
        description = f"{spot['spotName']}是{spot['scenicAreaName']}路线中的景点{stay_text}。"
    return {**spot, "description": description, "chunks": chunks}


@router.get("/{spot_id}/nearby")
async def get_nearby_spots(spot_id: str):
    spots = _spot_map()
    spot = spots.get(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    nearby = []
    for related in spot.get("relatedSpots", []):
        if isinstance(related, dict):
            related_id = related.get("spotId", "")
            related_name = related.get("spotName", related_id)
        else:
            related_id = ""
            related_name = str(related)

        matched = next(
            (
                item
                for item in spots.values()
                if item.get("spotId") == related_id or item.get("spotName") == related_name
            ),
            None,
        )
        if matched:
            nearby.append(
                {
                    "spotId": matched.get("spotId"),
                    "spotName": matched.get("spotName"),
                    "visualFeatures": matched.get("visualFeatures", []),
                }
            )
        else:
            nearby.append({"spotId": related_id or related_name, "spotName": related_name, "visualFeatures": []})

    return {"spotId": spot_id, "nearby": nearby}
