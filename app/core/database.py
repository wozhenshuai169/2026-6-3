import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Iterator

from app.core.config import settings

_init_lock = Lock()
_initialized_path: str | None = None

_MIGRATION_1 = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    normalized_name TEXT NOT NULL UNIQUE,
    user_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('tourist', 'guide', 'admin')),
    account_type TEXT NOT NULL DEFAULT 'account',
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS rooms (
    room_id TEXT PRIMARY KEY,
    leader_id TEXT NOT NULL REFERENCES users(user_id),
    room_name TEXT NOT NULL,
    scenic_area_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    current_spot TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status);
CREATE TABLE IF NOT EXISTS room_members (
    room_id TEXT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (room_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_room_members_user_id ON room_members(user_id);
CREATE TABLE IF NOT EXISTS room_messages (
    message_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    user_name TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL CHECK (message_type IN ('user', 'ai', 'system', 'broadcast')),
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_room_messages_room_created
    ON room_messages(room_id, created_at DESC, message_id DESC);
"""

_MIGRATION_2 = """
CREATE TABLE IF NOT EXISTS ws_tickets (
    ticket_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    room_id TEXT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL,
    used_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_ws_tickets_expires_at ON ws_tickets(expires_at);
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
    scene TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(room_id, user_id, scene)
);
CREATE TABLE IF NOT EXISTS operation_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    success INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_type_created ON operation_events(event_type, created_at DESC);
CREATE TABLE IF NOT EXISTS kb_documents (
    doc_id TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    file_name TEXT NOT NULL UNIQUE,
    file_url TEXT NOT NULL,
    suffix TEXT NOT NULL,
    size INTEGER NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    uploaded_at INTEGER NOT NULL,
    indexed_at INTEGER
);
CREATE TABLE IF NOT EXISTS kb_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT REFERENCES kb_documents(doc_id) ON DELETE CASCADE,
    spot_id TEXT,
    title TEXT NOT NULL,
    topic TEXT,
    source TEXT,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_doc ON kb_chunks(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunks_fts USING fts5(
    chunk_id UNINDEXED, title, content, source, tokenize='trigram'
);
"""

MIGRATIONS = ((1, _MIGRATION_1), (2, _MIGRATION_2))


def _open(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=10, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'virtual table') AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row["name"] == column for row in connection.execute(f"PRAGMA table_info({table})"))


def _has_application_schema(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
          AND name != 'schema_migrations'
        LIMIT 1
        """
    ).fetchone()
    return row is not None


def _backup_database(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target = backup_dir / f"{path.stem}-{stamp}.db"
    source = sqlite3.connect(str(path))
    destination = sqlite3.connect(str(target))
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def initialize_database() -> None:
    global _initialized_path
    path_obj = Path(settings.database_path).resolve()
    path = str(path_obj)
    if _initialized_path == path:
        return
    with _init_lock:
        if _initialized_path == path:
            return
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        connection = _open(path)
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            had_schema = _has_application_schema(connection)
            had_migration_table = _table_exists(connection, "schema_migrations")
            if had_schema and not had_migration_table:
                connection.close()
                _backup_database(path_obj)
                connection = _open(path)
                connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at INTEGER NOT NULL)"
            )
            connection.commit()
            applied = {row["version"] for row in connection.execute("SELECT version FROM schema_migrations")}
            pending = [item for item in MIGRATIONS if item[0] not in applied]
            if pending and had_schema and had_migration_table:
                connection.close()
                _backup_database(path_obj)
                connection = _open(path)
                connection.execute("PRAGMA journal_mode = WAL")
            for version, sql in pending:
                alter_legacy_users = (
                    version == 1
                    and _table_exists(connection, "users")
                    and not _column_exists(connection, "users", "account_type")
                )
                statements = ["BEGIN IMMEDIATE;", sql]
                if alter_legacy_users:
                    statements.append(
                        "ALTER TABLE users ADD COLUMN account_type TEXT NOT NULL DEFAULT 'account';"
                    )
                statements.append(
                    "INSERT INTO schema_migrations (version, applied_at) "
                    f"VALUES ({int(version)}, strftime('%s','now'));"
                )
                statements.append("COMMIT;")
                try:
                    connection.executescript("\n".join(statements))
                except Exception:
                    if connection.in_transaction:
                        connection.rollback()
                    raise
        finally:
            connection.close()
        _initialized_path = path


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    initialize_database()
    connection = _open(str(Path(settings.database_path).resolve()))
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def database_ready() -> bool:
    try:
        with database() as connection:
            connection.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False


def reset_database_initialization_for_tests() -> None:
    global _initialized_path
    _initialized_path = None
