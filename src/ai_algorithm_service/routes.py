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
        for route in self.data.routes:
            route_tags = set(route.get("tags", []))
            score = 0.45 + 0.12 * len(route_tags & desired_tags)
            if state.currentSpotId in route.get("spotIds", []):
                score += 0.1
            score = min(score, 0.96)
            reason = self._reason(route, route_tags & desired_tags)
            recommendations.append(
                RouteRecommendation(
                    routeId=route["routeId"],
                    title=route["title"],
                    score=round(score, 2),
                    reason=reason,
                    tags=route.get("tags", []),
                )
            )
        return sorted(recommendations, key=lambda item: item.score, reverse=True)[:limit]

    def _reason(self, route: dict, matched: set[str]) -> str:
        if "less_walking" in matched:
            return f"{route['title']}步行压力较低，适合当前体力状态。"
        if "history" in matched or "architecture" in matched:
            return f"{route['title']}覆盖历史和建筑讲解点，匹配兴趣画像。"
        if "family_friendly" in matched:
            return f"{route['title']}节奏平稳，适合有老人或儿童同行。"
        return f"{route['title']}适合作为当前景点后的常规游览路线。"

