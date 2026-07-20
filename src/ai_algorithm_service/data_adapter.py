from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any


class ScenicDataAdapter:
    """Local scenic data adapter.

    The interface mirrors future scenic management data sources, while the
    implementation reads the verified repository knowledge set.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parents[2] / "data"

    def _load_json(self, name: str) -> Any:
        with (self.data_dir / name).open("r", encoding="utf-8") as f:
            return json.load(f)

    @cached_property
    def chunks(self) -> list[dict[str, Any]]:
        return self._load_json("scenic_chunks.json")

    @cached_property
    def explanations(self) -> list[dict[str, Any]]:
        return self._load_json("explanations.json")

    @cached_property
    def routes(self) -> list[dict[str, Any]]:
        return self._load_json("routes.json")

    @cached_property
    def vision_spots(self) -> list[dict[str, Any]]:
        return self._load_json("vision_spots.json")

    @cached_property
    def eval_cases(self) -> list[dict[str, Any]]:
        return self._load_json("eval_cases.json")

    @cached_property
    def operation_events(self) -> list[dict[str, Any]]:
        return self._load_optional_json("operation_events.json")

    @cached_property
    def path_nodes(self) -> list[dict[str, Any]]:
        return self._load_optional_json("path_nodes.json")

    @cached_property
    def path_edges(self) -> list[dict[str, Any]]:
        return self._load_optional_json("path_edges.json")

    def _load_optional_json(self, name: str) -> Any:
        path = self.data_dir / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_spot_chunks(self, spot_id: str) -> list[dict[str, Any]]:
        return [chunk for chunk in self.chunks if chunk.get("spotId") == spot_id]

    def get_next_segment(self, current_segment_id: str) -> dict[str, Any] | None:
        ordered = sorted(self.explanations, key=lambda item: item["segmentId"])
        for index, segment in enumerate(ordered):
            if segment["segmentId"] == current_segment_id:
                return ordered[min(index + 1, len(ordered) - 1)]
        return ordered[0] if ordered else None

    def get_facility_hint(self, text: str, current_spot_id: str) -> dict[str, Any] | None:
        facility_words = ["厕所", "厕锁", "洗手间", "卫生间", "茅房", "休息", "歇会", "累了", "出口", "饮水", "口渴", "水", "服务台"]
        if not any(word in text for word in facility_words):
            return None
        spot_chunks = self.get_spot_chunks(current_spot_id)
        candidates = [chunk for chunk in spot_chunks + self.chunks if chunk.get("type") == "facility"]
        for chunk in candidates:
            haystack = "".join([chunk.get("title", ""), chunk.get("content", ""), chunk.get("topic", "")])
            if any(word in haystack for word in facility_words if word in text):
                return chunk
        return candidates[0] if candidates else None

    def query_operation_events(self, text: str, current_spot_id: str, current_route_id: str) -> list[dict[str, Any]]:
        event_words = {
            "route_closed": ["封路", "路线封闭", "不能走", "关闭"],
            "weather_alert": ["天气", "暴雨", "下雨", "雷电", "台风"],
            "crowd_warning": ["人流", "拥挤", "排队", "人多"],
            "announcement": ["公告", "通知", "开放", "活动"],
            "facility_closed": ["厕所关闭", "休息区关闭", "设施关闭"],
        }
        matched_types = [
            event_type
            for event_type, keywords in event_words.items()
            if any(keyword in text for keyword in keywords)
        ]
        if not matched_types:
            return []
        results: list[dict[str, Any]] = []
        for event in self.operation_events:
            if event.get("status", "active") != "active":
                continue
            if matched_types and event.get("eventType") not in matched_types:
                continue
            affected_spots = event.get("affectedSpotIds", [])
            affected_routes = event.get("affectedRouteIds", [])
            if affected_spots and current_spot_id not in affected_spots:
                continue
            if affected_routes and current_route_id not in affected_routes:
                continue
            results.append(event)
        return results

    def find_nearest_facility_path(self, current_spot_id: str, facility_type: str = "rest_area") -> dict[str, Any] | None:
        spot_node = next((node for node in self.path_nodes if node.get("spotId") == current_spot_id), None)
        if not spot_node:
            return None
        target_nodes = [
            node for node in self.path_nodes
            if node.get("nodeType") == facility_type or node.get("facilityType") == facility_type
        ]
        if not target_nodes:
            return None
        open_edges = [edge for edge in self.path_edges if edge.get("status", "open") == "open"]
        best: dict[str, Any] | None = None
        for target in target_nodes:
            score = self._shortest_minutes(spot_node["nodeId"], target["nodeId"], open_edges, avoid_high=True)
            if score is None:
                continue
            if best is None or score < best["walkingMinutes"]:
                best = {
                    "fromNodeId": spot_node["nodeId"],
                    "toNodeId": target["nodeId"],
                    "targetName": target["nodeName"],
                    "walkingMinutes": score,
                    "lowIntensity": True,
                    "verificationStatus": target.get("verificationStatus", "unknown"),
                    "verificationNote": target.get("verificationNote", ""),
                }
        return best

    def _shortest_minutes(
        self,
        start_node_id: str,
        target_node_id: str,
        edges: list[dict[str, Any]],
        avoid_high: bool = False,
    ) -> int | None:
        distances: dict[str, int] = {start_node_id: 0}
        visited: set[str] = set()
        while True:
            current = None
            current_distance = None
            for node_id, distance in distances.items():
                if node_id not in visited and (current_distance is None or distance < current_distance):
                    current = node_id
                    current_distance = distance
            if current is None or current_distance is None:
                return None
            if current == target_node_id:
                return current_distance
            visited.add(current)
            for edge in edges:
                if avoid_high and edge.get("difficulty") == "high":
                    continue
                left = edge.get("fromNodeId")
                right = edge.get("toNodeId")
                if current == left:
                    next_node = right
                elif current == right:
                    next_node = left
                else:
                    continue
                if not next_node:
                    continue
                next_distance = current_distance + int(edge.get("walkingMinutes", 999))
                if next_distance < distances.get(next_node, 10**9):
                    distances[next_node] = next_distance
