import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/spots")
DATA_DIR = Path("data")


def _load_json(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _spot_map() -> dict[str, dict]:
    return {item.get("spotId", ""): item for item in _load_json("vision_spots.json")}


@router.get("/{spot_id}")
async def get_spot(spot_id: str):
    spots = _spot_map()
    spot = spots.get(spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    chunks = [
        {
            "chunkId": chunk.get("chunkId"),
            "title": chunk.get("title"),
            "topic": chunk.get("topic"),
            "content": chunk.get("content"),
        }
        for chunk in _load_json("scenic_chunks.json")
        if chunk.get("spotId") == spot_id
    ][:8]
    return {**spot, "chunks": chunks}


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
