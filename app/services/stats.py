import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from math import ceil
from time import time
from typing import Any
from uuid import uuid4

from app.core.database import database


SERVICE_EVENT_TYPES = {
    "public_question",
    "public_voice_question",
    "solo_voice_question",
    "solo_question",
    "vision_recognize",
    "route_recommend",
    "room_narration",
}

SPOT_NAMES = {
    "lingshan_dazhaobi": "灵山大照壁",
    "wuming_bridge": "五明桥",
    "buddha_foot_altar": "佛足坛",
    "wuzhi_gate": "五智门",
    "bodhi_avenue": "菩提大道",
    "jiulong_guanyu": "九龙灌浴",
    "demon_relief": "降魔浮雕",
    "ashoka_pillar": "阿育王柱",
    "baizi_mile": "百子戏弥勒",
    "xiangfu_temple": "祥符禅寺",
    "lingshan_buddha": "灵山大佛",
    "buddhist_museum": "佛教文化博览馆",
    "lingshan_palace": "灵山梵宫",
    "wuyin_mandala": "五印坛城",
    "manfeilong_pagoda": "曼飞龙塔",
    "wujinyi_house": "无尽意斋",
}


def _period_starts() -> tuple[int, int]:
    now = datetime.now().astimezone()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = today - timedelta(days=today.weekday())
    return int(today.timestamp()), int(week.timestamp())


def _day_starts(days: int = 7) -> list[datetime]:
    today = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return [today - timedelta(days=offset) for offset in reversed(range(days))]


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


def _events(event_types: set[str] | None = None, since: int | None = None) -> list[dict]:
    clauses: list[str] = []
    params: list[Any] = []
    if event_types:
        placeholders = ",".join("?" for _ in event_types)
        clauses.append(f"event_type IN ({placeholders})")
        params.extend(sorted(event_types))
    if since is not None:
        clauses.append("created_at >= ?")
        params.append(since)
    query = "SELECT * FROM operation_events"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at ASC"
    with database() as connection:
        rows = connection.execute(query, params).fetchall()
    results = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, json.JSONDecodeError):
            payload = {}
        results.append(
            {
                "eventType": row["event_type"],
                "success": bool(row["success"]),
                "latencyMs": float(row["latency_ms"]),
                "payload": payload,
                "timestamp": int(row["created_at"]),
            }
        )
    return results


def _daily_event_trend(events: list[dict]) -> list[dict]:
    result = []
    for start in _day_starts():
        end = start + timedelta(days=1)
        start_ts, end_ts = int(start.timestamp()), int(end.timestamp())
        day_events = [item for item in events if start_ts <= item["timestamp"] < end_ts]
        result.append(
            {
                "date": start.date().isoformat(),
                "label": start.strftime("%m-%d"),
                "textCount": sum(item["eventType"] in {"public_question", "solo_question"} for item in day_events),
                "voiceCount": sum(item["eventType"] in {"public_voice_question", "solo_voice_question"} for item in day_events),
                "serviceCount": len(day_events),
            }
        )
    return result


def get_overview(active_rooms: int = 0, visitor_count: int = 0) -> dict[str, Any]:
    today_start, week_start = _period_starts()
    week_events = _events(SERVICE_EVENT_TYPES, since=week_start)
    today_events = [item for item in week_events if item["timestamp"] >= today_start]
    counts = Counter(item["eventType"] for item in today_events)
    return {
        "todayVisitors": visitor_count,
        "activeRooms": active_rooms,
        "todayServiceCount": len(today_events),
        "weekServiceCount": len(week_events),
        "questionCount": counts["public_question"] + counts["solo_question"],
        "voiceQuestionCount": counts["public_voice_question"] + counts["solo_voice_question"],
        "visionRecognizeCount": counts["vision_recognize"],
        "routeRecommendCount": counts["route_recommend"],
        "trend": _daily_event_trend(week_events),
    }


def get_hot_questions() -> list[dict[str, Any]]:
    _, week_start = _period_starts()
    counter: Counter[str] = Counter()
    for event in _events({"public_question", "public_voice_question"}, since=week_start):
        question = event["payload"].get("question") or event["payload"].get("asrText")
        if question:
            counter[str(question)] += 1
    return [{"question": text, "count": count} for text, count in counter.most_common(10)]


def get_hot_spots() -> list[dict[str, Any]]:
    _, week_start = _period_starts()
    counter: Counter[str] = Counter()
    for event in _events(SERVICE_EVENT_TYPES, since=week_start):
        spot = event["payload"].get("spotId") or event["payload"].get("currentSpot")
        if spot:
            counter[str(spot)] += 1
    return [
        {"spotId": spot, "spotName": SPOT_NAMES.get(spot, spot), "count": count}
        for spot, count in counter.most_common(10)
    ]


def get_satisfaction() -> dict[str, Any]:
    with database() as connection:
        rows = connection.execute(
            "SELECT score, emotion, created_at FROM feedback ORDER BY created_at"
        ).fetchall()
    total = len(rows)
    weighted = sum(int(row["score"]) for row in rows)
    distribution = Counter(str(row["score"]) for row in rows)
    emotion = Counter(str(row["emotion"] or "neutral") for row in rows)
    trend = []
    for start in _day_starts():
        end = start + timedelta(days=1)
        day_scores = [
            int(row["score"])
            for row in rows
            if int(start.timestamp()) <= int(row["created_at"]) < int(end.timestamp())
        ]
        trend.append(
            {
                "date": start.date().isoformat(),
                "label": start.strftime("%m-%d"),
                "averageScore": round(sum(day_scores) / len(day_scores), 2) if day_scores else None,
                "count": len(day_scores),
            }
        )
    return {
        "averageScore": round(weighted / total, 2) if total else 0.0,
        "totalResponses": total,
        "distribution": dict(distribution),
        "trend": trend,
        "emotion": {key: emotion.get(key, 0) for key in ("positive", "neutral", "negative")},
    }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(len(ordered) * percentile) - 1))
    return round(ordered[index], 2)


def get_system_metrics() -> dict[str, Any]:
    _, week_start = _period_starts()
    events = _events(since=week_start)
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    for event in events:
        grouped[event["eventType"]].append(event)
    total = len(events)
    success_total = sum(1 for event in events if event["success"])
    latencies = [event["latencyMs"] for event in events]
    interaction_latencies = [
        event["latencyMs"] for event in events if event["eventType"] in SERVICE_EVENT_TYPES
    ]
    return {
        "successRate": round(success_total / total, 4) if total else 0.0,
        "averageLatencyMs": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "p50LatencyMs": _percentile(interaction_latencies, 0.5),
        "p95LatencyMs": _percentile(interaction_latencies, 0.95),
        "under5SecondsRate": (
            round(sum(value < 5000 for value in interaction_latencies) / len(interaction_latencies), 4)
            if interaction_latencies
            else 0.0
        ),
        "totalCalls": total,
        "byEndpoint": [
            {
                "eventType": event_type,
                "success": sum(1 for item in items if item["success"]),
                "failure": sum(1 for item in items if not item["success"]),
                "averageLatencyMs": round(
                    sum(item["latencyMs"] for item in items) / len(items), 2
                ),
                "p95LatencyMs": _percentile([item["latencyMs"] for item in items], 0.95),
            }
            for event_type, items in sorted(grouped.items())
        ],
    }


def get_visitor_report() -> dict[str, Any]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT score, comment, tags_json, emotion, created_at
            FROM feedback ORDER BY updated_at DESC
            """
        ).fetchall()
    tag_counter: Counter[str] = Counter()
    tag_scores: defaultdict[str, list[int]] = defaultdict(list)
    recent_feedback = []
    for row in rows:
        try:
            tags = json.loads(row["tags_json"] or "[]")
        except json.JSONDecodeError:
            tags = []
        for tag in tags:
            tag_counter[str(tag)] += 1
            tag_scores[str(tag)].append(int(row["score"]))
        if row["comment"] and len(recent_feedback) < 8:
            recent_feedback.append(
                {
                    "score": int(row["score"]),
                    "comment": str(row["comment"]),
                    "tags": tags,
                    "emotion": str(row["emotion"]),
                    "createdAt": int(row["created_at"]),
                }
            )

    _, week_start = _period_starts()
    topic_counter: Counter[str] = Counter()
    for event in _events(SERVICE_EVENT_TYPES, since=week_start):
        topic = event["payload"].get("topic")
        if topic:
            topic_counter[str(topic)] += 1

    emotion = Counter(str(row["emotion"] or "neutral") for row in rows)
    suggestions = []
    for tag, scores in tag_scores.items():
        average = sum(scores) / len(scores)
        if len(scores) >= 2 and average < 3.5:
            suggestions.append(f"“{tag}”相关反馈平均为{average:.1f}分，建议优先复查近期低分记录。")
    metrics = get_system_metrics()
    if metrics["totalCalls"] and metrics["successRate"] < 0.95:
        suggestions.append("近一周服务成功率低于95%，建议先查看失败次数较多的服务并核对外部接口状态。")
    if metrics["p95LatencyMs"] >= 5000:
        suggestions.append("近一周交互的95分位耗时超过5秒，建议重点排查语音识别、问答和语音合成链路。")
    if not suggestions:
        suggestions.append("当前没有形成明确的低分集中项；继续收集文字反馈后再决定优化优先级。")

    return {
        "feedbackCount": len(rows),
        "attentionTopics": [
            {"topic": topic, "count": count}
            for topic, count in (topic_counter + tag_counter).most_common(8)
        ],
        "emotionDistribution": {
            key: emotion.get(key, 0) for key in ("positive", "neutral", "negative")
        },
        "sentimentTrend": get_satisfaction()["trend"],
        "serviceSuggestions": suggestions,
        "recentFeedback": recent_feedback,
    }
