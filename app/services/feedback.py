from time import time
from uuid import uuid4

from app.core.database import database


def upsert_feedback(room_id: str, user_id: str, score: int, scene: str) -> dict:
    now = int(time())
    feedback_id = uuid4().hex
    with database() as connection:
        existing = connection.execute(
            "SELECT feedback_id FROM feedback WHERE room_id = ? AND user_id = ? AND scene = ?",
            (room_id, user_id, scene),
        ).fetchone()
        if existing:
            feedback_id = existing["feedback_id"]
            connection.execute(
                "UPDATE feedback SET score = ?, updated_at = ? WHERE feedback_id = ?",
                (score, now, feedback_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO feedback (feedback_id, room_id, user_id, score, scene, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (feedback_id, room_id, user_id, score, scene, now, now),
            )
    return {"feedbackId": feedback_id, "score": score, "status": "saved"}
