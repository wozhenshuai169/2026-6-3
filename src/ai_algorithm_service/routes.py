from __future__ import annotations

from .data_adapter import ScenicDataAdapter
from .schemas import RouteRecommendation, TouristProfile, TourState


class RouteRecommender:
    def __init__(self, data: ScenicDataAdapter) -> None:
        self.data = data

    def recommend(self, profile: TouristProfile, state: TourState, limit: int = 3) -> list[RouteRecommendation]:
        memory = profile.memoryTags or {}
        desired_tags = set(profile.interests)
        desired_tags.update(memory.get("interest", []))
        desired_tags.update(memory.get("routePreference", []))
        if memory.get("stamina") == "low":
            desired_tags.add("less_walking")
        if any(companion in ["child", "elderly"] for companion in profile.companions + memory.get("companions", [])):
            desired_tags.add("family_friendly")

        recommendations: list[RouteRecommendation] = []
        closed_route_ids = {
            route_id
            for event in self.data.operation_events
            if event.get("status", "active") == "active"
            and event.get("eventType") == "route_closed"
            and event.get("severity") == "critical"
            for route_id in event.get("affectedRouteIds", [])
        }
        for route in self.data.routes:
            if route["routeId"] in closed_route_ids:
                continue
            route_tags = set(route.get("tags", []))
            matched = sorted(route_tags & desired_tags)
            breakdown = {
                "interestScore": 3 if route_tags & desired_tags else 0,
                "timeScore": self._time_score(route, memory),
                "staminaScore": 2 if ("less_walking" in desired_tags and route.get("walkingDifficulty") == "low") else 0,
                "companionScore": 2 if ("family_friendly" in desired_tags and route.get("suitableForChildren") and route.get("suitableForElderly")) else 0,
                "distanceScore": 1 if state.currentSpotId in route.get("spotIds", []) else 0,
            }
            score = sum(breakdown.values())
            if state.currentSpotId in route.get("spotIds", []):
                matched.append("current_spot")
            reason = self._reason(route, set(matched), breakdown)
            recommendations.append(
                RouteRecommendation(
                    routeId=route["routeId"],
                    title=route["title"],
                    score=score,
                    reason=reason,
                    tags=route.get("tags", []),
                    durationMinutes=route.get("durationMinutes"),
                    difficulty=route.get("difficulty"),
                    spotIds=route.get("spotIds", []),
                    matchedPreferences=sorted(set(matched)),
                    scoreBreakdown=breakdown,
                )
            )
        return sorted(recommendations, key=lambda item: item.score, reverse=True)[:limit]

    def _time_score(self, route: dict, memory: dict) -> int:
        available = memory.get("availableMinutes") or memory.get("timeMinutes")
        if not available:
            return 2 if route.get("durationMinutes", 999) <= 60 else 0
        return 2 if route.get("durationMinutes", 999) <= int(available) else 0

    def _reason(self, route: dict, matched: set[str], breakdown: dict[str, int]) -> str:
        if "less_walking" in matched:
            return f"{route['title']}步行压力较低，比较适合当前体力和同行情况。"
        if "history" in matched or "architecture" in matched:
            return f"{route['title']}包含较多历史和建筑讲解点，更贴合你的兴趣。"
        if "family_friendly" in matched or "family" in matched:
            return f"{route['title']}节奏比较平稳，适合与老人或儿童一起游览。"
        if "nature" in matched:
            return f"{route['title']}串联林荫步道与开阔景观，适合边走边欣赏自然环境。"
        return f"{route['title']}与当前可用时间较匹配，可以作为本次游览安排。"
