import hashlib
import hmac
import secrets
from time import time
from uuid import uuid4

from app.core.config import settings

users: dict[str, dict] = {}
_user_ids_by_name: dict[str, str] = {}
_sessions: dict[str, dict] = {}


def _normalize_name(user_name: str) -> str:
    return user_name.strip().casefold()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


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


def _create_session(user: dict) -> dict:
    token = secrets.token_urlsafe(32)
    expires_at = int(time()) + settings.session_ttl_seconds
    _sessions[token] = {"userId": user["userId"], "expiresAt": expires_at}
    return {
        "userId": user["userId"],
        "userName": user["userName"],
        "role": user["role"],
        "token": token,
        "expiresAt": expires_at,
    }


def register_user(user_name: str, password: str, role: str = "tourist") -> dict:
    clean_name = user_name.strip()
    normalized_name = _normalize_name(clean_name)
    if not normalized_name:
        raise ValueError("User name cannot be empty")
    if normalized_name in _user_ids_by_name:
        raise KeyError("User name already exists")
    if role not in {"tourist", "guide", "admin"}:
        raise ValueError("Invalid role")

    user_id = str(uuid4())
    user = {
        "userId": user_id,
        "userName": clean_name,
        "passwordHash": _hash_password(password),
        "role": role,
        "createdAt": int(time()),
    }
    users[user_id] = user
    _user_ids_by_name[normalized_name] = user_id
    return _create_session(user)


def login_user(user_name: str, password: str) -> dict | None:
    user_id = _user_ids_by_name.get(_normalize_name(user_name))
    user = users.get(user_id or "")
    if user is None or not _verify_password(password, user["passwordHash"]):
        return None
    return _create_session(user)


def get_user_by_token(token: str) -> dict | None:
    session = _sessions.get(token)
    if session is None:
        return None
    if session["expiresAt"] <= int(time()):
        _sessions.pop(token, None)
        return None
    return users.get(session["userId"])


def revoke_token(token: str) -> None:
    _sessions.pop(token, None)


def ensure_bootstrap_admin() -> None:
    if not settings.admin_user_name or not settings.admin_password:
        return
    if _normalize_name(settings.admin_user_name) in _user_ids_by_name:
        return
    register_user(settings.admin_user_name, settings.admin_password, role="admin")
