"""Single product-facing adapter for the algorithm core.

The public FastAPI schemas stay in ``app.schemas``.  This module only maps
persisted room/profile state into the shared algorithm models and maps route
recommendations back into the legacy product shape.
"""

from __future__ import annotations

import heapq
from typing import Any

try:  # Installed package and pytest's ``pythonpath = src`` path.
    from ai_algorithm_service.data_adapter import ScenicDataAdapter
    from ai_algorithm_service.decision import DecisionRouter
    from ai_algorithm_service.explanation import TourExplanation
    from ai_algorithm_service.memory import MemoryExtractor
    from ai_algorithm_service.private_assistant import PrivateAssistant
    from ai_algorithm_service.routes import RouteRecommender
    from ai_algorithm_service.schemas import AlgorithmRequest, TouristProfile, TourState
except ModuleNotFoundError:  # ``uvicorn app.main:app`` from a source checkout.
    from src.ai_algorithm_service.data_adapter import ScenicDataAdapter
    from src.ai_algorithm_service.decision import DecisionRouter
    from src.ai_algorithm_service.explanation import TourExplanation
    from src.ai_algorithm_service.memory import MemoryExtractor
    from src.ai_algorithm_service.private_assistant import PrivateAssistant
    from src.ai_algorithm_service.routes import RouteRecommender
    from src.ai_algorithm_service.schemas import AlgorithmRequest, TouristProfile, TourState


_INTEREST_ALIASES = {
    "历史": "history",
    "人文": "history",
    "建筑": "architecture",
    "古建": "architecture",
    "深度讲解": "deep_explanation",
    "少走路": "less_walking",
    "亲子": "family_friendly",
}


class AlgorithmFacade:
    """The only algorithm entry point used by the product service layer."""

    def __init__(self) -> None:
        self.data = ScenicDataAdapter()
        self.decision_router = DecisionRouter()
        self.explanation = TourExplanation(self.data)
        self.memory = MemoryExtractor()
        self.private_assistant = PrivateAssistant(self.data, self.memory)
        self.route_recommender = RouteRecommender(self.data)

    def request(
        self,
        room: dict,
        user_id: str,
        *,
        channel: str = "public",
        text: str = "",
        input_mode: str = "text",
        asr_confidence: float | None = None,
        image_url: str | None = None,
        memory_tags: dict | None = None,
        interests: list[str] | None = None,
        companions: list[str] | None = None,
    ) -> AlgorithmRequest:
        state = TourState(
            roomId=room["roomId"],
            currentSpotId=room.get("currentSpot") or "main_hall",
            currentRouteId=room.get("routeId") or "classic",
            isExplaining=room.get("status") == "active",
            phase=room.get("status", "active"),
        )
        profile = TouristProfile(
            touristId=user_id,
            memoryTags=memory_tags or {},
            interests=interests or [],
            companions=companions or [],
        )
        return AlgorithmRequest(
            roomId=room["roomId"],
            userId=user_id,
            channel=channel,
            text=text,
            inputMode=input_mode,
            asrConfidence=asr_confidence,
            imageUrl=image_url,
            state=state,
            profile=profile,
        )

    def decide(self, request: AlgorithmRequest):
        return self.decision_router.decide(request)

    def extract_memory(self, text: str) -> dict:
        return self.memory.extract(text)

    def private_answer(self, request: AlgorithmRequest):
        return self.private_assistant.handle(request)

    def resume_after_answer(self, request: AlgorithmRequest, answer: str) -> dict:
        return self.explanation.resume_after_answer(request.state, request.text, answer)

    def recommend(
        self,
        room: dict,
        user_id: str,
        preferences: dict | None,
        memory_tags: dict | None,
    ) -> dict:
        preferences = preferences or {}
        profile_memory = dict(memory_tags or {})
        profile_memory["availableMinutes"] = preferences.get("timeLimit", 60)
        if preferences.get("physicalStrength") == "low":
            profile_memory["stamina"] = "low"
        companions = list(profile_memory.get("companions", []))
        if preferences.get("withChildren"):
            companions.append("child")
        if preferences.get("withElderly"):
            companions.append("elderly")
        interests = [_INTEREST_ALIASES.get(value, value) for value in preferences.get("interest", [])]
        request = self.request(
            room,
            user_id,
            channel="private",
            text="推荐路线",
            memory_tags=profile_memory,
            interests=interests,
            companions=list(dict.fromkeys(companions)),
        )
        routes = self.route_recommender.recommend(request.profile, request.state)
        if not routes:
            return {
                "routeId": "",
                "routeName": "暂无可用路线",
                "score": 0.0,
                "estimatedTime": 0,
                "spots": [],
                "reason": "当前没有满足条件的开放路线，请联系团长确认。",
                "distance": 0.0,
                "difficulty": "",
                "matchedPreferences": [],
                "scoreBreakdown": {},
            }
        top = routes[0]
        return {
            "routeId": top.routeId,
            "routeName": top.title,
            "score": float(top.score),
            "estimatedTime": int(top.durationMinutes or 0),
            "spots": [self._route_spot(spot_id) for spot_id in top.spotIds],
            "reason": top.reason,
            "distance": self._route_distance(top.spotIds),
            "difficulty": top.difficulty or "",
            "matchedPreferences": top.matchedPreferences,
            "scoreBreakdown": {key: float(value) for key, value in top.scoreBreakdown.items()},
        }

    def _route_spot(self, spot_id: str) -> dict:
        names = {item.get("spotId"): item.get("spotName") for item in self.data.vision_spots}
        for node in self.data.path_nodes:
            names.setdefault(node.get("spotId"), node.get("nodeName"))
        return {
            "spotId": spot_id,
            "spotName": names.get(spot_id) or spot_id,
            "stayMinutes": self._suggested_stay_minutes(spot_id),
        }

    def _suggested_stay_minutes(self, spot_id: str) -> int:
        for route in self.data.routes:
            if spot_id in route.get("spotIds", []):
                return max(5, int(route.get("durationMinutes", 30)) // max(1, len(route["spotIds"])))
        return 10

    def _route_distance(self, spot_ids: list[str]) -> float:
        nodes = {node.get("spotId"): node.get("nodeId") for node in self.data.path_nodes if node.get("spotId")}
        total_meters = 0
        for start, end in zip(spot_ids, spot_ids[1:]):
            distance = self._shortest_distance(nodes.get(start), nodes.get(end))
            if distance is not None:
                total_meters += distance
        return round(total_meters / 1000, 2)

    def _shortest_distance(self, start: str | None, target: str | None) -> int | None:
        if not start or not target:
            return None
        adjacency: dict[str, list[tuple[str, int]]] = {}
        for edge in self.data.path_edges:
            if edge.get("status", "open") != "open":
                continue
            left, right = edge.get("fromNodeId"), edge.get("toNodeId")
            meters = int(edge.get("distanceMeters", 0))
            if left and right and meters > 0:
                adjacency.setdefault(left, []).append((right, meters))
                adjacency.setdefault(right, []).append((left, meters))
        queue: list[tuple[int, str]] = [(0, start)]
        costs: dict[str, int] = {start: 0}
        while queue:
            cost, node = heapq.heappop(queue)
            if node == target:
                return cost
            if cost != costs.get(node):
                continue
            for next_node, edge_cost in adjacency.get(node, []):
                next_cost = cost + edge_cost
                if next_cost < costs.get(next_node, 10**12):
                    costs[next_node] = next_cost
                    heapq.heappush(queue, (next_cost, next_node))
        return None


algorithm_facade = AlgorithmFacade()
