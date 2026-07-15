"""高德 Web 服务 Provider。

API Key 只在后端请求中使用，不会下发到浏览器，也不会写入日志。
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from time import monotonic

import httpx

from app.core.config import settings
from app.providers.base import MapProvider, RouteResult


logger = logging.getLogger(__name__)


class AmapProviderError(RuntimeError):
    """高德 API 返回错误、超时或数据不完整。"""


class AmapMapProvider(MapProvider):
    provider_name = "amap"
    data_source = "高德地图 Web 服务"

    def __init__(self) -> None:
        if not settings.map_api_key:
            raise RuntimeError("MAP_API_KEY 未配置")
        self._api_key = settings.map_api_key
        self._base_url = settings.map_base_url.rstrip("/")
        self._timeout = settings.map_timeout
        self._cache_ttl = max(0, settings.map_cache_ttl_seconds)
        self._min_interval = max(0, settings.map_min_request_interval_ms) / 1000
        self._cache: dict[str, tuple[float, dict]] = {}
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def _request(self, path: str, params: dict) -> dict:
        safe_params = {key: value for key, value in params.items() if key != "key"}
        cache_key = f"{path}:{json.dumps(safe_params, ensure_ascii=False, sort_keys=True)}"
        cached = self._cache.get(cache_key)
        if cached and monotonic() - cached[0] <= self._cache_ttl:
            logger.info("[Map][AMap] 命中缓存 service=%s", path)
            return cached[1]

        for attempt in range(3):
            async with self._request_lock:
                wait_seconds = self._min_interval - (monotonic() - self._last_request_at)
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                logger.info("[Map][AMap] 请求 service=%s attempt=%d", path, attempt + 1)
                try:
                    async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
                        response = await client.get(path, params={"key": self._api_key, **safe_params})
                    self._last_request_at = monotonic()
                except httpx.TimeoutException as exc:
                    raise AmapProviderError("高德地图请求超时，请稍后重试") from exc
                except httpx.HTTPError as exc:
                    raise AmapProviderError("无法连接高德地图服务，请检查服务器网络") from exc

            if response.status_code >= 400:
                raise AmapProviderError(f"高德地图 HTTP 服务异常（{response.status_code}）")
            try:
                payload = response.json()
            except ValueError as exc:
                raise AmapProviderError("高德地图返回了无法解析的数据") from exc

            if payload.get("status") == "1":
                self._cache[cache_key] = (monotonic(), payload)
                logger.info("[Map][AMap] 成功 service=%s count=%s", path, payload.get("count", "-"))
                return payload

            info = str(payload.get("info") or "UNKNOWN_ERROR")
            if "QPS" in info and attempt < 2:
                await asyncio.sleep(0.6 * (attempt + 1))
                continue
            raise AmapProviderError(f"高德地图调用失败：{info}")

        raise AmapProviderError("高德地图调用频率受限，请稍后重试")

    @staticmethod
    def _parse_location(value: str | None) -> tuple[float | None, float | None]:
        if not value or "," not in value:
            return None, None
        try:
            longitude, latitude = value.split(",", 1)
            return float(longitude), float(latitude)
        except (TypeError, ValueError):
            return None, None

    @classmethod
    def _normalise_poi(cls, poi: dict) -> dict:
        longitude, latitude = cls._parse_location(poi.get("location"))
        navi = poi.get("navi") if isinstance(poi.get("navi"), dict) else {}
        return {
            "poiId": str(poi.get("id") or ""),
            "name": str(poi.get("name") or ""),
            "longitude": longitude,
            "latitude": latitude,
            "address": str(poi.get("address") or ""),
            "province": str(poi.get("pname") or ""),
            "city": str(poi.get("cityname") or ""),
            "district": str(poi.get("adname") or ""),
            "type": str(poi.get("type") or ""),
            "typeCode": str(poi.get("typecode") or ""),
            "entranceLocation": str(navi.get("entr_location") or ""),
            "temporarilyClosed": "暂停开放" in str(poi.get("name") or ""),
            "dataSource": cls.data_source,
        }

    async def search_pois(
        self,
        keywords: str,
        *,
        city: str = "无锡市",
        page_size: int = 10,
    ) -> list[dict]:
        payload = await self._request(
            "/v5/place/text",
            {
                "keywords": keywords,
                "region": city,
                "city_limit": "true",
                "show_fields": "navi,business",
                "page_size": min(max(page_size, 1), 25),
                "page_num": 1,
            },
        )
        return [self._normalise_poi(poi) for poi in payload.get("pois", [])]

    @staticmethod
    def _plain_name(value: str) -> str:
        value = re.sub(r"[（(].*?[）)]", "", value)
        value = value.replace("灵山胜境", "")
        return re.sub(r"[\s·・—_-]", "", value).lower()

    def select_best_poi(self, pois: list[dict], target_name: str) -> dict | None:
        target = self._plain_name(target_name)

        def score(poi: dict) -> int:
            name = self._plain_name(str(poi.get("name") or ""))
            if name == target:
                return 100
            if target and target in name:
                return 80
            if name and name in target:
                return 60
            return 0

        ranked = sorted(pois, key=score, reverse=True)
        return ranked[0] if ranked and score(ranked[0]) >= 60 else None

    async def _resolve_poi(self, spot_name: str, *, city: str, scenic_name: str) -> dict:
        pois = await self.search_pois(f"{scenic_name}-{spot_name}", city=city, page_size=10)
        matched = self.select_best_poi(pois, spot_name)
        if not matched:
            pois = await self.search_pois(spot_name, city=city, page_size=10)
            matched = self.select_best_poi(pois, spot_name)
        if not matched or matched.get("longitude") is None or matched.get("latitude") is None:
            raise AmapProviderError(f"高德地图未找到“{spot_name}”的可信坐标")
        return matched

    async def _walking_route(self, origin: str, destination: str) -> dict:
        payload = await self._request(
            "/v5/direction/walking",
            {
                "origin": origin,
                "destination": destination,
                "show_fields": "cost,polyline",
            },
        )
        paths = (payload.get("route") or {}).get("paths") or []
        if not paths:
            raise AmapProviderError("高德地图未返回可用的园内步行路线")
        path = paths[0]
        steps = path.get("steps") or []
        return {
            "distanceMeters": int(float(path.get("distance") or 0)),
            "durationSeconds": int(float((path.get("cost") or {}).get("duration") or 0)),
            "steps": steps,
        }

    async def plan_route(self, spot_ids: list[str], preferences: dict) -> RouteResult:
        """根据资料中的景点名称查真实 POI，再用高德规划相邻步行路线。"""

        city = str(preferences.get("city") or "无锡市")
        scenic_name = str(preferences.get("scenicAreaName") or "灵山胜境")
        metadata = preferences.get("stopMetadata") or {}
        resolved: list[dict] = []
        for spot_name in spot_ids:
            poi = await self._resolve_poi(spot_name, city=city, scenic_name=scenic_name)
            meta = metadata.get(spot_name) or {}
            resolved.append(
                {
                    "spotId": str(meta.get("spotId") or poi["poiId"]),
                    "spotName": spot_name,
                    "stayMinutes": int(meta.get("stayMinutes") or 10),
                    "poiId": poi["poiId"],
                    "amapPoiName": poi["name"],
                    "longitude": poi["longitude"],
                    "latitude": poi["latitude"],
                    "address": poi["address"],
                    "district": poi["district"],
                    "temporarilyClosed": poi["temporarilyClosed"],
                    "dataSource": self.data_source,
                }
            )

        total_distance = 0
        total_duration = 0
        polyline: list[str] = []
        instructions: list[dict] = []
        for start, end in zip(resolved, resolved[1:]):
            origin = f"{start['longitude']:.6f},{start['latitude']:.6f}"
            destination = f"{end['longitude']:.6f},{end['latitude']:.6f}"
            leg = await self._walking_route(origin, destination)
            total_distance += leg["distanceMeters"]
            total_duration += leg["durationSeconds"]
            leg_instructions: list[str] = []
            for step in leg["steps"]:
                instruction = str(step.get("instruction") or "")
                if instruction:
                    leg_instructions.append(instruction)
                step_polyline = str(step.get("polyline") or "")
                if step_polyline:
                    polyline.extend(point for point in step_polyline.split(";") if point)
            instructions.append(
                {
                    "fromSpot": start["spotName"],
                    "toSpot": end["spotName"],
                    "distanceMeters": leg["distanceMeters"],
                    "durationMinutes": max(1, math.ceil(leg["durationSeconds"] / 60)),
                    "instructions": leg_instructions,
                }
            )

        stay_minutes = sum(spot["stayMinutes"] for spot in resolved)
        estimated_time = stay_minutes + math.ceil(total_duration / 60)
        return RouteResult(
            route_name=str(preferences.get("routeName") or f"{scenic_name}推荐路线"),
            estimated_time=estimated_time,
            spots=resolved,
            reason=str(preferences.get("reason") or "景点坐标、步行距离和路线均来自高德地图实时服务。"),
            distance=round(total_distance / 1000, 2),
            difficulty=str(preferences.get("difficulty") or "medium"),
            route_polyline=polyline,
            instructions=instructions,
            map_provider=self.provider_name,
            data_source=self.data_source,
        )
