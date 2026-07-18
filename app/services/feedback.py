import json
from time import time
from uuid import uuid4

from app.core.database import database


def _emotion(score: int, comment: str) -> str:
    positive_words = ["很好", "喜欢", "清楚", "方便", "满意", "生动", "有帮助"]
    negative_words = ["卡顿", "听不清", "太快", "错误", "没反应", "不好", "不满意", "绕路"]
    positive = sum(word in comment for word in positive_words)
    negative = sum(word in comment for word in negative_words)
    if negative > positive:
        return "negative"
    if positive > negative:
        return "positive"
    if score >= 4:
        return "positive"
    if score <= 2:
        return "negative"
    return "neutral"


def upsert_feedback(
    room_id: str,
    user_id: str,
    score: int,
    scene: str,
    comment: str = "",
    tags: list[str] | None = None,
) -> dict:
    now = int(time())
    feedback_id = uuid4().hex
    clean_comment = comment.strip()
    clean_tags = list(dict.fromkeys(tags or []))
    emotion = _emotion(score, clean_comment)
    with database() as connection:
        existing = connection.execute(
            "SELECT feedback_id FROM feedback WHERE room_id = ? AND user_id = ? AND scene = ?",
            (room_id, user_id, scene),
        ).fetchone()
        if existing:
            feedback_id = existing["feedback_id"]
            connection.execute(
                """
                UPDATE feedback
                SET score = ?, comment = ?, tags_json = ?, emotion = ?, updated_at = ?
                WHERE feedback_id = ?
                """,
                (score, clean_comment, json.dumps(clean_tags, ensure_ascii=False), emotion, now, feedback_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO feedback (
                    feedback_id, room_id, user_id, score, scene, comment,
                    tags_json, emotion, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id, room_id, user_id, score, scene, clean_comment,
                    json.dumps(clean_tags, ensure_ascii=False), emotion, now, now,
                ),
            )
    return {
        "feedbackId": feedback_id,
        "score": score,
        "comment": clean_comment,
        "tags": clean_tags,
        "emotion": emotion,
        "status": "saved",
    }
