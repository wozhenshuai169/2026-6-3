from time import time

from app.core.database import database


def _serialize(row) -> dict:
    return {
        "role": row["role"],
        "outfit": row["outfit"],
        "imageUrl": row["image_url"],
        "voice": row["voice"],
        "speed": float(row["speed"]),
        "emotion": row["emotion"],
        "lipSync": bool(row["lip_sync"]),
        "emotionSync": bool(row["emotion_sync"]),
        "idleMotion": bool(row["idle_motion"]),
        "updatedAt": int(row["updated_at"]),
    }


def get_avatar_settings() -> dict:
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM avatar_settings WHERE config_id = 'default'"
        ).fetchone()
    if row is None:
        raise RuntimeError("讲解形象设置尚未初始化")
    return _serialize(row)


def save_avatar_settings(values: dict) -> dict:
    updated_at = int(time())
    with database() as connection:
        connection.execute(
            """
            INSERT INTO avatar_settings (
                config_id, role, outfit, image_url, voice, speed, emotion,
                lip_sync, emotion_sync, idle_motion, updated_at
            ) VALUES ('default', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(config_id) DO UPDATE SET
                role = excluded.role,
                outfit = excluded.outfit,
                image_url = excluded.image_url,
                voice = excluded.voice,
                speed = excluded.speed,
                emotion = excluded.emotion,
                lip_sync = excluded.lip_sync,
                emotion_sync = excluded.emotion_sync,
                idle_motion = excluded.idle_motion,
                updated_at = excluded.updated_at
            """,
            (
                values["role"], values["outfit"], values["imageUrl"], values["voice"], values["speed"],
                values["emotion"], int(values["lipSync"]), int(values["emotionSync"]),
                int(values["idleMotion"]), updated_at,
            ),
        )
    return get_avatar_settings()


def save_avatar_image(image_url: str) -> dict:
    with database() as connection:
        connection.execute(
            "UPDATE avatar_settings SET image_url = ?, updated_at = ? WHERE config_id = 'default'",
            (image_url, int(time())),
        )
    return get_avatar_settings()
