"""Lightweight in-memory stats for demo dashboards."""

from __future__ import annotations

from collections import Counter, defaultdict
from time import time
from typing import Any

_events: list[dict[str, Any]] = []
_latencies: defaultdict[str, list[float]] = defaultdict(list)
_success: Counter[str] = Counter()
_failure: Counter[str] = Counter()

_DEFAULT_OVERVIEW = {
    "todayVisitors": 36,
    "activeRooms": 3,
    "questionCount": 128,
    "voiceQuestionCount": 42,
    "visionRecognizeCount": 17,
    "routeRecommendCount": 9,
}


def record_event(
    event_type: str,
    success: bool = True,
    latency_ms: float = 0,
    payload: dict[str, Any] | None = None,
) -> None:
    event = {
        "eventType": event_type,
        "success": success,
        "latencyMs": round(float(latency_ms), 2),
        "payload": payload or {},
        "timestamp": time(),
    }
    _events.append(event)
    _latencies[event_type].append(event["latencyMs"])
    if success:
        _success[event_type] += 1
    else:
        _failure[event_type] += 1


def get_overview(active_rooms: int = 0, visitor_count: int = 0) -> dict[str, Any]:
    real = {
        "todayVisitors": visitor_count,
        "activeRooms": active_rooms,
        "questionCount": _success["public_question"] + _failure["public_question"],
        "voiceQuestionCount": _success["public_voice_question"] + _failure["public_voice_question"],
        "visionRecognizeCount": _success["vision_recognize"] + _failure["vision_recognize"],
        "routeRecommendCount": _success["route_recommend"] + _failure["route_recommend"],
    }
    return {key: value or _DEFAULT_OVERVIEW[key] for key, value in real.items()}


def get_hot_questions() -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for event in _events:
        if event["eventType"] in {"public_question", "public_voice_question"}:
            question = event["payload"].get("question") or event["payload"].get("asrText")
            if question:
                counter[str(question)] += 1
    if not counter:
        return [
            {"question": "这个建筑是什么时候建的？", "count": 18},
            {"question": "附近哪里可以休息？", "count": 12},
            {"question": "推荐一条少走路的路线", "count": 9},
        ]
    return [{"question": text, "count": count} for text, count in counter.most_common(10)]


def get_hot_spots() -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for event in _events:
        spot = event["payload"].get("spotId") or event["payload"].get("currentSpot")
        if spot:
            counter[str(spot)] += 1
    if not counter:
        return [
            {"spotId": "main_hall", "spotName": "主展厅", "count": 28},
            {"spotId": "bell_tower", "spotName": "钟楼", "count": 19},
            {"spotId": "courtyard", "spotName": "中心庭院", "count": 15},
        ]
    return [{"spotId": spot, "spotName": spot, "count": count} for spot, count in counter.most_common(10)]


def get_satisfaction() -> dict[str, Any]:
    return {
        "averageScore": 4.7,
        "trend": [
            {"time": "09:00", "score": 4.5},
            {"time": "11:00", "score": 4.8},
            {"time": "14:00", "score": 4.7},
            {"time": "16:00", "score": 4.9},
        ],
        "emotion": {"friendly": 72, "neutral": 18, "thinking": 7, "surprised": 3},
    }


def get_system_metrics() -> dict[str, Any]:
    total_success = sum(_success.values())
    total_failure = sum(_failure.values())
    total = total_success + total_failure
    success_rate = round(total_success / total, 4) if total else 0.96
    all_latencies = [item for values in _latencies.values() for item in values]
    avg_latency = round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 820.0
    return {
        "successRate": success_rate,
        "averageLatencyMs": avg_latency,
        "totalCalls": total or 216,
        "byEndpoint": [
            {
                "eventType": event_type,
                "success": _success[event_type],
                "failure": _failure[event_type],
                "averageLatencyMs": round(sum(values) / len(values), 2) if values else 0,
            }
            for event_type, values in sorted(_latencies.items())
        ],
    }
