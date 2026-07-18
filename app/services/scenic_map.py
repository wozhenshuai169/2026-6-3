"""灵山胜境与高德地图的产品服务层。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.errors import AppError
from app.providers.factory import get_map
from app.providers.map.amap import AmapMapProvider, AmapProviderError


SCENIC_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "scenic_areas.json"


@lru_cache(maxsize=1)
def _scenic_data() -> dict:
    return json.loads(SCENIC_DATA_PATH.read_text(encoding="utf-8"))


def get_scenic_area(scenic_area_id: str) -> dict:
    for area in _scenic_data().get("scenicAreas", []):
        if area.get("scenicAreaId") == scenic_area_id:
            return area
    raise AppError(404, "SCENIC_AREA_NOT_FOUND", "未找到指定景区")


def get_default_scenic_area() -> dict:
    return get_scenic_area(_scenic_data()["defaultScenicAreaId"])


def list_route_templates(scenic_area_id: str) -> list[dict]:
    return get_scenic_area(scenic_area_id).get("routeTemplates", [])


def _real_map_provider() -> AmapMapProvider:
    try:
        provider = get_map()
    except RuntimeError as exc:
        raise AppError(503, "MAP_NOT_CONFIGURED", str(exc)) from exc
    if not isinstance(provider, AmapMapProvider):
        raise AppError(503, "MAP_PROVIDER_INVALID", "当前没有启用真实高德地图服务")
    return provider


def _public_area(area: dict, poi: dict) -> dict:
    return {
        "scenicAreaId": area["scenicAreaId"],
        "scenicAreaName": area["scenicAreaName"],
        "city": area["city"],
        "district": poi.get("district") or area.get("district", ""),
        "address": poi.get("address", ""),
        "longitude": poi.get("longitude"),
        "latitude": poi.get("latitude"),
        "entranceLocation": poi.get("entranceLocation", ""),
        "poiId": poi.get("poiId", ""),
        "amapPoiName": poi.get("name", ""),
        "temporarilyClosed": poi.get("temporarilyClosed", False),
        "isPrimary": bool(area.get("isPrimary")),
        "dataSource": "高德地图 Web 服务",
    }


async def get_current_scenic_context() -> dict:
    provider = _real_map_provider()
    current = get_default_scenic_area()
    try:
        pois = await provider.search_pois(current["searchKeyword"], city=current["city"], page_size=10)
        primary_poi = provider.select_best_poi(pois, current["scenicAreaName"])
        if not primary_poi:
            raise AmapProviderError("高德地图未找到灵山胜境主景区")

        related = []
        for area in _scenic_data().get("scenicAreas", []):
            if area.get("scenicAreaId") == current["scenicAreaId"]:
                continue
            area_pois = await provider.search_pois(area["searchKeyword"], city=area["city"], page_size=5)
            area_poi = provider.select_best_poi(area_pois, area["scenicAreaName"]) or (
                area_pois[0] if area_pois else None
            )
            if area_poi:
                related.append(_public_area(area, area_poi))
        return {
            "mapProvider": "amap",
            "dataSource": "高德地图 Web 服务",
            "current": _public_area(current, primary_poi),
            "relatedScenicAreas": related,
            "pois": pois,
        }
    except AmapProviderError as exc:
        raise AppError(502, "AMAP_REQUEST_FAILED", str(exc)) from exc


def _select_route_template(area: dict, preferences: dict) -> dict:
    templates = sorted(area.get("routeTemplates", []), key=lambda item: int(item.get("maxMinutes", 999)))
    if not templates:
        raise AppError(422, "SCENIC_ROUTE_MISSING", "该景区尚未配置路线模板")
    time_limit = int(preferences.get("timeLimit") or 60)
    eligible = [item for item in templates if int(item.get("maxMinutes", 999)) <= time_limit]
    candidates = eligible or [templates[0]]
    interests = set(preferences.get("interest") or [])
    if "family_friendly" in interests:
        interests.add("family")
    low_intensity = preferences.get("physicalStrength") == "low" or preferences.get("withElderly")
    with_children = bool(preferences.get("withChildren"))

    def score(template: dict) -> tuple[int, int]:
        tags = set(template.get("tags") or [])
        value = len(tags & interests) * 6
        if low_intensity:
            value += 8 if template.get("difficulty") == "low" else 0
            value += 3 if "less_walking" in tags else 0
            value += 5 if int(template.get("maxMinutes", 999)) <= 60 else 0
        if with_children:
            value += 10 if {"family", "family_friendly"} & tags else 0
        # When preferences are otherwise equal, make fuller use of the chosen time.
        return value, int(template.get("maxMinutes", 0))

    return max(candidates, key=score)


async def recommend_scenic_route(scenic_area_id: str, preferences: dict) -> dict:
    area = get_scenic_area(scenic_area_id)
    template = _select_route_template(area, preferences)
    provider = _real_map_provider()
    stops = template.get("spots", [])
    stop_metadata = {item["name"]: item for item in stops}
    interests = set(preferences.get("interest") or [])
    if preferences.get("withChildren"):
        interests.add("family")
    if preferences.get("physicalStrength") == "low" or preferences.get("withElderly"):
        interests.add("less_walking")
    matched = sorted(interests & set(template.get("tags", [])))
    reason = (
        f"结合你的兴趣、游览时间和同行情况，推荐“{template['title']}”。"
        "路线仅安排灵山胜境内的景点，途中请留意现场指引和临时通行提示。"
    )
    try:
        planned = await provider.plan_route(
            [item["name"] for item in stops],
            {
                "city": area["city"],
                "scenicAreaName": area["scenicAreaName"],
                "routeName": template["title"],
                "difficulty": template.get("difficulty", "medium"),
                "stopMetadata": stop_metadata,
                "reason": reason,
            },
        )
    except AmapProviderError as exc:
        raise AppError(502, "AMAP_ROUTE_FAILED", str(exc)) from exc

    time_limit = int(preferences.get("timeLimit") or 60)
    breakdown = {
        "interestScore": min(4, len(matched) * 2),
        "timeScore": 2 if planned.estimated_time <= time_limit else 0,
        "staminaScore": 2 if preferences.get("physicalStrength") == "low" and planned.difficulty == "low" else 0,
        "companionScore": 2 if preferences.get("withChildren") or preferences.get("withElderly") else 0,
        "distanceScore": 1 if planned.distance <= 2 else 0,
    }
    return {
        "routeId": template["routeId"],
        "routeName": planned.route_name,
        "score": float(sum(breakdown.values())),
        "estimatedTime": planned.estimated_time,
        "spots": planned.spots,
        "reason": planned.reason,
        "distance": planned.distance,
        "difficulty": planned.difficulty,
        "matchedPreferences": matched,
        "scoreBreakdown": breakdown,
        "scenicAreaId": area["scenicAreaId"],
        "scenicAreaName": area["scenicAreaName"],
        "mapProvider": planned.map_provider,
        "dataSource": planned.data_source,
        "routePolyline": planned.route_polyline,
        "instructions": planned.instructions,
    }
