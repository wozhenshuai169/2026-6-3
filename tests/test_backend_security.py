import sqlite3
from time import time

import pytest

from app.core.config import settings
from app.core.database import (
    database,
    initialize_database,
    reset_database_initialization_for_tests,
)
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit, reset_rate_limits_for_tests
from app.services.users import get_user_by_id


def test_password_token_storage_expiry_and_identity_spoofing(client, auth_helpers):
    tourist = auth_helpers["register"]("tourist", "secure")
    guide = auth_helpers["register"]("guide", "secure-guide")
    headers = auth_helpers["headers"]
    stored = get_user_by_id(tourist["userId"])
    assert "password" not in stored
    assert stored["passwordHash"].startswith("pbkdf2_sha256$")
    with database() as connection:
        plain = connection.execute(
            "SELECT COUNT(*) AS total FROM sessions WHERE token_hash = ?", (tourist["token"],)
        ).fetchone()["total"]
        connection.execute(
            "UPDATE sessions SET expires_at = ? WHERE user_id = ?",
            (int(time()) - 1, tourist["userId"]),
        )
    assert plain == 0
    assert client.get("/api/auth/me", headers=headers(tourist)).status_code == 401

    tourist = auth_helpers["register"]("tourist", "spoof")
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    forged = client.post(
        "/api/ai/public-question",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": guide["userId"],
            "question": "forged",
            "needAudio": False,
        },
    )
    assert forged.status_code == 403
    assert forged.json()["errorCode"] == "IDENTITY_MISMATCH"


def test_rate_limit_returns_retry_after():
    previous = settings.rate_limit_enabled
    settings.rate_limit_enabled = True
    reset_rate_limits_for_tests()
    try:
        enforce_rate_limit("test", "identity", 1, 60)
        with pytest.raises(AppError) as caught:
            enforce_rate_limit("test", "identity", 1, 60)
        assert caught.value.status_code == 429
        assert int(caught.value.headers["Retry-After"]) >= 1
    finally:
        settings.rate_limit_enabled = previous
        reset_rate_limits_for_tests()


def test_new_database_migrations_are_idempotent(tmp_path):
    previous = settings.database_path
    path = tmp_path / "fresh.db"
    try:
        settings.database_path = str(path)
        reset_database_initialization_for_tests()
        initialize_database()
        reset_database_initialization_for_tests()
        initialize_database()
        connection = sqlite3.connect(path)
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        connection.close()
        assert versions == [(1,), (2,), (3,)]
    finally:
        settings.database_path = previous
        reset_database_initialization_for_tests()


def test_legacy_database_is_backed_up_and_upgraded(tmp_path):
    previous = settings.database_path
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            normalized_name TEXT NOT NULL UNIQUE,
            user_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        INSERT INTO users VALUES ('u1', 'legacy', 'Legacy', 'hash', 'tourist', 1);
        """
    )
    connection.close()
    try:
        settings.database_path = str(path)
        reset_database_initialization_for_tests()
        initialize_database()
        backup_files = list((tmp_path / "backups").glob("legacy-*.db"))
        assert len(backup_files) == 1
        backup = sqlite3.connect(backup_files[0])
        assert backup.execute("SELECT user_name FROM users").fetchone()[0] == "Legacy"
        assert backup.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'schema_migrations'"
        ).fetchone() is None
        backup.close()
        upgraded = sqlite3.connect(path)
        columns = {row[1] for row in upgraded.execute("PRAGMA table_info(users)")}
        assert "account_type" in columns
        assert upgraded.execute("SELECT user_name FROM users WHERE user_id = 'u1'").fetchone()[0] == "Legacy"
        upgraded.close()
    finally:
        settings.database_path = previous
        reset_database_initialization_for_tests()


def test_versioned_database_is_backed_up_before_next_version(tmp_path, monkeypatch):
    import app.core.database as database_module

    previous_path = settings.database_path
    all_migrations = database_module.MIGRATIONS
    path = tmp_path / "versioned.db"
    try:
        settings.database_path = str(path)
        monkeypatch.setattr(database_module, "MIGRATIONS", all_migrations[:1])
        reset_database_initialization_for_tests()
        initialize_database()
        monkeypatch.setattr(database_module, "MIGRATIONS", all_migrations)
        reset_database_initialization_for_tests()
        initialize_database()
        backups = list((tmp_path / "backups").glob("versioned-*.db"))
        assert len(backups) == 1
        backup = sqlite3.connect(backups[0])
        assert backup.execute("SELECT version FROM schema_migrations").fetchall() == [(1,)]
        assert backup.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'ws_tickets'"
        ).fetchone() is None
        backup.close()
    finally:
        database_module.MIGRATIONS = all_migrations
        settings.database_path = previous_path
        reset_database_initialization_for_tests()


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    import app.core.database as database_module

    previous_path = settings.database_path
    previous_migrations = database_module.MIGRATIONS
    path = tmp_path / "rollback.db"
    monkeypatch.setattr(
        database_module,
        "MIGRATIONS",
        ((99, "CREATE TABLE partial_write (id INTEGER); INVALID SQL;"),),
    )
    try:
        settings.database_path = str(path)
        reset_database_initialization_for_tests()
        with pytest.raises(sqlite3.Error):
            initialize_database()
        connection = sqlite3.connect(path)
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'partial_write'"
        ).fetchone() is None
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 0
        connection.close()
    finally:
        database_module.MIGRATIONS = previous_migrations
        settings.database_path = previous_path
        reset_database_initialization_for_tests()
