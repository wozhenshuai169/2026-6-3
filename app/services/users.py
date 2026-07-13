import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime
from time import time
from uuid import uuid4

from app.core.config import settings
from app.core.database import database


def _normalize_name(user_name: str) -> str:
    return user_name.strip().casefold()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return "pbkdf2_sha256$" + salt.hex() + "$" + digest.hex()


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_hex, expected_hex = encoded.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 310_000
        )
        return hmac.compare_digest(actual.hex(), expected_hex)
    except (TypeError, ValueError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _row_to_user(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {
        "userId": row["user_id"],
        "userName": row["user_name"],
        "passwordHash": row["password_hash"],
        "role": row["role"],
        "accountType": row["account_type"],
        "createdAt": row["created_at"],
    }


def _create_session(user: dict, ttl_seconds: int | None = None) -> dict:
    token = secrets.token_urlsafe(32)
    now = int(time())
    expires_at = now + (ttl_seconds or settings.session_ttl_seconds)
    with database() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), user["userId"], expires_at, now),
        )
    return {
        "userId": user["userId"],
        "userName": user["userName"],
        "role": user["role"],
        "token": token,
        "expiresAt": expires_at,
    }


def register_user(
    user_name: str,
    password: str,
    role: str = "tourist",
    account_type: str = "account",
) -> dict:
    clean_name = user_name.strip()
    normalized_name = _normalize_name(clean_name)
    if not normalized_name:
        raise ValueError("User name cannot be empty")
    if role not in {"tourist", "guide", "admin"}:
        raise ValueError("Invalid role")

    user = {
        "userId": str(uuid4()),
        "userName": clean_name,
        "passwordHash": _hash_password(password),
        "role": role,
        "accountType": account_type,
        "createdAt": int(time()),
    }
    try:
        with database() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    user_id, normalized_name, user_name, password_hash, role, account_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["userId"],
                    normalized_name,
                    user["userName"],
                    user["passwordHash"],
                    role,
                    account_type,
                    user["createdAt"],
                ),
            )
    except sqlite3.IntegrityError as exc:
        if "normalized_name" in str(exc) or "UNIQUE constraint failed" in str(exc):
            raise KeyError("User name already exists") from exc
        raise
    return _create_session(user)


def create_guest_session(display_name: str, role: str) -> dict:
    if role not in {"tourist", "guide"}:
        raise ValueError("Guest role must be tourist or guide")
    clean_name = display_name.strip()
    if not clean_name:
        raise ValueError("Display name cannot be empty")
    guest_key = f"guest:{uuid4().hex}"
    user = {
        "userId": str(uuid4()),
        "userName": clean_name,
        "passwordHash": _hash_password(secrets.token_urlsafe(32)),
        "role": role,
        "accountType": "guest",
        "createdAt": int(time()),
    }
    with database() as connection:
        connection.execute(
            """
            INSERT INTO users (
                user_id, normalized_name, user_name, password_hash, role, account_type, created_at
            ) VALUES (?, ?, ?, ?, ?, 'guest', ?)
            """,
            (
                user["userId"], guest_key, user["userName"], user["passwordHash"],
                role, user["createdAt"],
            ),
        )
    return _create_session(user, settings.guest_ttl_seconds)


def login_user(user_name: str, password: str) -> dict | None:
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE normalized_name = ?",
            (_normalize_name(user_name),),
        ).fetchone()
    user = _row_to_user(row)
    if user is None or not _verify_password(password, user["passwordHash"]):
        return None
    return _create_session(user)


def get_user_by_token(token: str) -> dict | None:
    if not token:
        return None
    now = int(time())
    token_hash = _token_hash(token)
    with database() as connection:
        row = connection.execute(
            """
            SELECT u.*
            FROM sessions AS s
            JOIN users AS u ON u.user_id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()
        if row is None:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ? OR expires_at <= ?",
                (token_hash, now),
            )
    return _row_to_user(row)


def get_user_by_id(user_id: str) -> dict | None:
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_user(row)


def revoke_token(token: str) -> None:
    with database() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


def create_ws_ticket(user_id: str, room_id: str) -> dict:
    ticket = secrets.token_urlsafe(32)
    expires_at = int(time()) + settings.ws_ticket_ttl_seconds
    with database() as connection:
        connection.execute(
            "INSERT INTO ws_tickets (ticket_hash, user_id, room_id, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(ticket), user_id, room_id, expires_at),
        )
    return {"ticket": ticket, "expiresAt": expires_at}


def consume_ws_ticket(ticket: str, room_id: str) -> dict | None:
    now = int(time())
    with database() as connection:
        row = connection.execute(
            """
            SELECT u.* FROM ws_tickets wt
            JOIN users u ON u.user_id = wt.user_id
            WHERE wt.ticket_hash = ? AND wt.room_id = ?
              AND wt.expires_at > ? AND wt.used_at IS NULL
            """,
            (_token_hash(ticket), room_id, now),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE ws_tickets SET used_at = ? WHERE ticket_hash = ?",
            (now, _token_hash(ticket)),
        )
    return _row_to_user(row)


def cleanup_auth_state() -> None:
    now = int(time())
    with database() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        connection.execute("DELETE FROM ws_tickets WHERE expires_at <= ? OR used_at IS NOT NULL", (now,))
        connection.execute(
            """
            DELETE FROM users
            WHERE account_type = 'guest'
              AND created_at < ?
              AND NOT EXISTS (SELECT 1 FROM sessions s WHERE s.user_id = users.user_id)
              AND NOT EXISTS (SELECT 1 FROM room_members rm WHERE rm.user_id = users.user_id)
              AND NOT EXISTS (SELECT 1 FROM rooms r WHERE r.leader_id = users.user_id)
            """,
            (now - settings.guest_ttl_seconds,),
        )


def count_users(today_only: bool = False) -> int:
    query = "SELECT COUNT(*) AS total FROM users"
    params: tuple = ()
    if today_only:
        start = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
        query += " WHERE created_at >= ?"
        params = (int(start.timestamp()),)
    with database() as connection:
        row = connection.execute(query, params).fetchone()
    return int(row["total"])


def ensure_bootstrap_admin() -> None:
    if not settings.admin_user_name or not settings.admin_password:
        return
    with database() as connection:
        exists = connection.execute(
            "SELECT 1 FROM users WHERE normalized_name = ?",
            (_normalize_name(settings.admin_user_name),),
        ).fetchone()
    if exists is not None:
        return
    session = register_user(settings.admin_user_name, settings.admin_password, role="admin")
    revoke_token(session["token"])
