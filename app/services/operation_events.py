"""Persisted, time-bounded operating notices for algorithm grounding."""

from __future__ import annotations

import json
from time import time
from uuid import uuid4

from app.core.database import database


def _event_dict(row) -> dict:
    return {
        "eventId": row["event_id"], "scenicAreaId": row["scenic_area_id"],
        "eventType": row["event_type"], "severity": row["severity"],
        "title": row["title"], "content": row["content"],
        "affectedSpotIds": json.loads(row["affected_spot_ids_json"]),
        "affectedRouteIds": json.loads(row["affected_route_ids_json"]),
        "status": row["status"], "validFrom": int(row["valid_from"]),
        "validUntil": int(row["valid_until"]) if row["valid_until"] is not None else None,
        "createdAt": int(row["created_at"]), "updatedAt": int(row["updated_at"]),
    }


def create_operation_event(payload: dict, creator_id: str) -> dict:
    now, event_id = int(time()), uuid4().hex
    with database() as connection:
        connection.execute(
            """INSERT INTO scenic_operation_events (event_id, scenic_area_id, event_type, severity, title, content,
            affected_spot_ids_json, affected_route_ids_json, status, valid_from, valid_until, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)""",
            (event_id, payload["scenicAreaId"], payload["eventType"], payload["severity"], payload["title"],
             payload["content"], json.dumps(payload.get("affectedSpotIds", []), ensure_ascii=False),
             json.dumps(payload.get("affectedRouteIds", []), ensure_ascii=False), now, payload.get("validUntil"),
             creator_id, now, now),
        )
        row = connection.execute("SELECT * FROM scenic_operation_events WHERE event_id = ?", (event_id,)).fetchone()
    return _event_dict(row)


def list_operation_events(scenic_area_id: str, active_only: bool = True) -> list[dict]:
    now = int(time())
    query, params = "SELECT * FROM scenic_operation_events WHERE scenic_area_id = ?", [scenic_area_id]
    if active_only:
        query += " AND status = 'active' AND valid_from <= ? AND (valid_until IS NULL OR valid_until >= ?)"
        params.extend([now, now])
    query += " ORDER BY severity = 'critical' DESC, updated_at DESC"
    with database() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_event_dict(row) for row in rows]


def update_operation_event_status(event_id: str, status: str) -> dict | None:
    with database() as connection:
        connection.execute("UPDATE scenic_operation_events SET status = ?, updated_at = ? WHERE event_id = ?", (status, int(time()), event_id))
        row = connection.execute("SELECT * FROM scenic_operation_events WHERE event_id = ?", (event_id,)).fetchone()
    return _event_dict(row) if row else None


def active_event_chunks(query: str) -> list[dict]:
    words = {"route_closed": ["封路", "封闭", "不能走", "关闭"], "weather_alert": ["天气", "暴雨", "下雨", "雷电", "台风"], "crowd_warning": ["人流", "拥挤", "排队", "人多"], "announcement": ["公告", "通知", "开放", "活动", "演出"], "facility_closed": ["厕所", "卫生间", "休息区", "设施"]}
    kinds = {kind for kind, terms in words.items() if any(term in query for term in terms)}
    if not kinds:
        return []
    events = [event for area in ("scenic_001", "lingshan_shengjing") for event in list_operation_events(area) if event["eventType"] in kinds]
    return [{"chunkId": f"event:{event['eventId']}", "title": event["title"], "source": "景区运营公告", "score": 1.0, "contentPreview": event["content"], "isRealtime": True} for event in events]
