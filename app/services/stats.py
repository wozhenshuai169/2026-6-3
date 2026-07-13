import json
from collections import Counter, defaultdict
from time import time
from typing import Any
from uuid import uuid4

from app.core.database import database


def record_event(
    event_type: str,
    success: bool = True,
    latency_ms: float = 0,
    payload: dict[str, Any] | None = None,
) -> None:
    with database() as connection:
        connection.execute(
            """
            INSERT INTO operation_events (
                event_id, event_type, success, latency_ms, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uuid4().hex,
                event_type,
                1 if success else 0,
                round(float(latency_ms), 2),
                json.dumps(payload or {}, ensure_ascii=False),
                int(time()),
            ),
        )


def _events(event_types: set[str] | None = None) -> list[dict]:
    query = "SELECT * FROM operation_events"
    params: list[str] = []
    if event_types:
        placeholders = ",".join("?" for _ in event_types)
        query += f" WHERE event_type IN ({placeholders})"
        params.extend(sorted(event_types))
    with database() as connection:
        rows = connection.execute(query, params).fetchall()
    return [
        {
            "eventType": row["event_type"],
            "success": bool(row["success"]),
            "latencyMs": row["latency_ms"],
            "payload": json.loads(row["payload_json"]),
            "timestamp": row["created_at"],
        }
        for row in rows
    ]


def get_overview(active_rooms: int = 0, visitor_count: int = 0) -> dict[str, Any]:
    with database() as connection:
        counts = {
            row["event_type"]: row["total"]
            for row in connection.execute(
                "SELECT event_type, COUNT(*) AS total FROM operation_events GROUP BY event_type"
            )
        }
    return {
        "todayVisitors": visitor_count,
        "activeRooms": active_rooms,
        "questionCount": counts.get("public_question", 0),
        "voiceQuestionCount": counts.get("public_voice_question", 0),
        "visionRecognizeCount": counts.get("vision_recognize", 0),
        "routeRecommendCount": counts.get("route_recommend", 0),
    }


def get_hot_questions() -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for event in _events({"public_question", "public_voice_question"}):
        question = event["payload"].get("question") or event["payload"].get("asrText")
        if question:
            counter[str(question)] += 1
    return [{"question": text, "count": count} for text, count in counter.most_common(10)]


def get_hot_spots() -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for event in _events():
        spot = event["payload"].get("spotId") or event["payload"].get("currentSpot")
        if spot:
            counter[str(spot)] += 1
    return [
        {"spotId": spot, "spotName": spot, "count": count}
        for spot, count in counter.most_common(10)
    ]


def get_satisfaction() -> dict[str, Any]:
    with database() as connection:
        rows = connection.execute(
            "SELECT score, COUNT(*) AS total FROM feedback GROUP BY score ORDER BY score"
        ).fetchall()
    total = sum(row["total"] for row in rows)
    weighted = sum(row["score"] * row["total"] for row in rows)
    return {
        "averageScore": round(weighted / total, 2) if total else 0.0,
        "totalResponses": total,
        "distribution": {str(row["score"]): row["total"] for row in rows},
        "trend": [],
        "emotion": {},
    }


def get_system_metrics() -> dict[str, Any]:
    events = _events()
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    for event in events:
        grouped[event["eventType"]].append(event)
    total = len(events)
    success_total = sum(1 for event in events if event["success"])
    latencies = [event["latencyMs"] for event in events]
    return {
        "successRate": round(success_total / total, 4) if total else 0.0,
        "averageLatencyMs": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "totalCalls": total,
        "byEndpoint": [
            {
                "eventType": event_type,
                "success": sum(1 for item in items if item["success"]),
                "failure": sum(1 for item in items if not item["success"]),
                "averageLatencyMs": round(
                    sum(item["latencyMs"] for item in items) / len(items), 2
                ),
            }
            for event_type, items in sorted(grouped.items())
        ],
    }
