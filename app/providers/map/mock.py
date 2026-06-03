"""Mock Map Provider —— 当地图 API Key 未设置时降级使用。

对齐 src/ai_algorithm_service/routes.py 的可解释加分制：
  interestScore (+3) / timeScore (+2) / staminaScore (+2) / companionScore (+2) / distanceScore (+1)
"""

import json
import logging
from pathlib import Path

from app.providers.base import MapProvider, RouteResult

logger = logging.getLogger(__name__)


def _load_routes() -> list[dict]:
    """从 data/routes.json 加载路线数据。"""
    routes_path = Path(__file__).resolve().parents[3] / "data" / "routes.json"
    if routes_path.exists():
        with open(routes_path, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("[Map] routes.json not found, using empty routes")
    return []


class MockMapProvider(MapProvider):
    """Mock 地图：基于可解释加分制推荐路线。"""

    def __init__(self) -> None:
        self._routes = _load_routes()
        logger.info("[Map] Using Mock (no map API key configured, %d routes)", len(self._routes))

    async def plan_route(self, spot_ids: list[str], preferences: dict) -> RouteResult:
        """根据偏好计算每条路线的分数，返回最高分路线。"""
        prefs = preferences or {}
        interest = prefs.get("interest", [])
        with_elderly = prefs.get("withElderly", False)
        with_children = prefs.get("withChildren", False)
        physical = prefs.get("physicalStrength", "medium")
        time_limit = prefs.get("timeLimit", 60)
        current_spot = spot_ids[0] if spot_ids else ""

        # 中→英标签映射（对齐 routes.json 的英文 tags）
        _TAG_MAP = {
            "历史": "history", "建筑": "architecture", "摄影": "photography",
            "亲子": "family", "休闲": "leisure", "文化": "culture",
            "自然": "nature", "摄影": "photography",
        }
        desired = set()
        for tag in interest:
            desired.add(_TAG_MAP.get(tag, tag))
        if physical == "low" or with_elderly:
            desired.add("less_walking")
        if with_children or with_elderly:
            desired.add("family_friendly")

        best: RouteResult | None = None
        best_score = -1

        for route in self._routes:
            route_tags = set(route.get("tags", []))
            matched = sorted(route_tags & desired)

            breakdown = {
                "interestScore": 3 if route_tags & desired else 0,
                "timeScore": 2 if route.get("durationMinutes", 999) <= time_limit else 0,
                "staminaScore": 2 if ("less_walking" in desired and route.get("walkingDifficulty") == "low") else 0,
                "companionScore": 2 if (
                    "family_friendly" in desired
                    and route.get("suitableForChildren")
                    and route.get("suitableForElderly")
                ) else 0,
                "distanceScore": 1 if current_spot and current_spot in route.get("spotIds", []) else 0,
            }
            score = sum(breakdown.values())

            if score > best_score:
                best_score = score
                # 构建理由文本
                score_text = "、".join(f"{k}={v}" for k, v in breakdown.items() if v)
                if "less_walking" in desired and route.get("walkingDifficulty") == "low":
                    reason = f"{route['title']}步行压力较低，适合当前体力状态；命中分数：{score_text}。"
                elif "history" in desired or "architecture" in desired:
                    reason = f"{route['title']}覆盖历史和建筑讲解点，匹配兴趣画像；命中分数：{score_text}。"
                elif "family_friendly" in desired:
                    reason = f"{route['title']}节奏平稳，适合有老人或儿童同行；命中分数：{score_text}。"
                else:
                    reason = f"{route['title']}适合作为当前景点后的常规游览路线；命中分数：{score_text or '基础匹配'}。"

                # 将 JSON 中的 spotIds 转换为 spots 列表
                spots = []
                for sid in route.get("spotIds", []):
                    spots.append({
                        "spotId": sid,
                        "spotName": sid,  # Mock 用 ID 作为名称
                        "stayMinutes": 10,
                    })

                best = RouteResult(
                    route_name=route["title"],
                    estimated_time=route.get("durationMinutes", 60),
                    spots=spots,
                    reason=reason,
                    distance=route.get("walkingDifficulty", "medium") == "low" and 1.2 or 1.8,
                    difficulty=route.get("difficulty", "medium"),
                    matched_preferences=sorted(matched),
                    score_breakdown=breakdown,
                )

        # fallback: no routes loaded
        if best is None:
            best = RouteResult(
                route_name="经典中轴线",
                estimated_time=60,
                spots=[
                    {"spotId": "spot_001", "spotName": "入口广场", "stayMinutes": 10},
                    {"spotId": "spot_002", "spotName": "主展厅", "stayMinutes": 20},
                    {"spotId": "spot_003", "spotName": "钟楼", "stayMinutes": 15},
                    {"spotId": "spot_004", "spotName": "鼓楼", "stayMinutes": 15},
                ],
                reason="经典中轴游览路线，覆盖景区核心景点，时间适中。",
                distance=1.8,
                difficulty="medium",
                matched_preferences=[],
                score_breakdown={"interestScore": 0, "timeScore": 0, "staminaScore": 0, "companionScore": 0, "distanceScore": 0},
            )

        return best
