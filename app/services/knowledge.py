import json
from io import BytesIO
from pathlib import Path
from time import time
from uuid import uuid4

from app.core.database import database

DATA_DIR = Path("data")
UPLOAD_DIR = Path("uploads") / "kb"


def _extract_text(content: bytes, suffix: str) -> str:
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8")
    if suffix == ".json":
        value = json.loads(content.decode("utf-8"))
        return json.dumps(value, ensure_ascii=False, indent=2)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF support requires the pypdf dependency") from exc
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Unsupported document type")


def _chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not clean:
        raise ValueError("Document contains no extractable text")
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        chunks.append(clean[start : start + size])
        if start + size >= len(clean):
            break
        start += size - overlap
    return chunks


def _delete_fts(connection, chunk_ids: list[str]) -> None:
    if not chunk_ids:
        return
    placeholders = ",".join("?" for _ in chunk_ids)
    connection.execute(f"DELETE FROM kb_chunks_fts WHERE chunk_id IN ({placeholders})", chunk_ids)


def index_document(doc_id: str) -> dict:
    with database() as connection:
        doc = connection.execute("SELECT * FROM kb_documents WHERE doc_id = ?", (doc_id,)).fetchone()
    if doc is None:
        raise KeyError("Document not found")
    path = UPLOAD_DIR / doc["file_name"]
    try:
        text = _extract_text(path.read_bytes(), doc["suffix"])
        pieces = _chunk_text(text)
        now = int(time())
        with database() as connection:
            old_ids = [
                row["chunk_id"]
                for row in connection.execute("SELECT chunk_id FROM kb_chunks WHERE doc_id = ?", (doc_id,))
            ]
            _delete_fts(connection, old_ids)
            connection.execute("DELETE FROM kb_chunks WHERE doc_id = ?", (doc_id,))
            for index, piece in enumerate(pieces):
                chunk_id = f"{doc_id}_{index:04d}"
                title = f"{doc['original_name']} #{index + 1}"
                connection.execute(
                    """
                    INSERT INTO kb_chunks (chunk_id, doc_id, title, source, content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, doc_id, title, doc["original_name"], piece, now),
                )
                connection.execute(
                    "INSERT INTO kb_chunks_fts (chunk_id, title, content, source) VALUES (?, ?, ?, ?)",
                    (chunk_id, title, piece, doc["original_name"]),
                )
            connection.execute(
                "UPDATE kb_documents SET status = 'indexed', error = NULL, indexed_at = ? WHERE doc_id = ?",
                (now, doc_id),
            )
        return {"docId": doc_id, "status": "indexed", "chunkCount": len(pieces)}
    except Exception as exc:
        with database() as connection:
            connection.execute(
                "UPDATE kb_documents SET status = 'failed', error = ? WHERE doc_id = ?",
                (str(exc)[:500], doc_id),
            )
        raise


def create_document(original_name: str, file_name: str, suffix: str, size: int) -> dict:
    doc_id = uuid4().hex
    uploaded_at = int(time())
    file_url = f"/uploads/kb/{file_name}"
    with database() as connection:
        connection.execute(
            """
            INSERT INTO kb_documents (
                doc_id, original_name, file_name, file_url, suffix, size, status, uploaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'uploaded', ?)
            """,
            (doc_id, original_name, file_name, file_url, suffix, size, uploaded_at),
        )
    index_document(doc_id)
    return get_document(doc_id)


def _doc_dict(row) -> dict:
    return {
        "docId": row["doc_id"],
        "originalName": row["original_name"],
        "fileName": row["file_name"],
        "fileUrl": row["file_url"],
        "suffix": row["suffix"],
        "size": row["size"],
        "status": row["status"],
        "error": row["error"],
        "uploadedAt": row["uploaded_at"],
        "indexedAt": row["indexed_at"],
    }


def list_documents() -> list[dict]:
    with database() as connection:
        rows = connection.execute("SELECT * FROM kb_documents ORDER BY uploaded_at DESC").fetchall()
    return [_doc_dict(row) for row in rows]


def get_document(doc_id: str) -> dict:
    with database() as connection:
        row = connection.execute("SELECT * FROM kb_documents WHERE doc_id = ?", (doc_id,)).fetchone()
        if row is None:
            raise KeyError("Document not found")
        chunk_count = connection.execute(
            "SELECT COUNT(*) AS total FROM kb_chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()["total"]
    result = _doc_dict(row)
    result["chunkCount"] = chunk_count
    return result


def delete_document(doc_id: str) -> None:
    with database() as connection:
        row = connection.execute("SELECT file_name FROM kb_documents WHERE doc_id = ?", (doc_id,)).fetchone()
        if row is None:
            raise KeyError("Document not found")
        chunk_ids = [
            item["chunk_id"]
            for item in connection.execute("SELECT chunk_id FROM kb_chunks WHERE doc_id = ?", (doc_id,))
        ]
        _delete_fts(connection, chunk_ids)
        connection.execute("DELETE FROM kb_documents WHERE doc_id = ?", (doc_id,))
    (UPLOAD_DIR / row["file_name"]).unlink(missing_ok=True)


def rebuild_index() -> dict:
    documents = list_documents()
    indexed = 0
    failed = 0
    for document in documents:
        try:
            index_document(document["docId"])
            indexed += 1
        except Exception:
            failed += 1
    return {"status": "rebuilt", "docCount": len(documents), "indexed": indexed, "failed": failed}


def seed_scenic_chunks() -> None:
    """Synchronize repository scenic knowledge without touching uploaded documents.

    Built-in chunks have ``doc_id IS NULL``. Replacing the JSON file must therefore
    replace those rows as a set; otherwise renamed or removed demo chunks remain in
    SQLite and can still be retrieved. Administrator-uploaded chunks always carry a
    document id and are deliberately preserved.
    """
    path = DATA_DIR / "scenic_chunks.json"
    if not path.exists():
        return
    chunks = json.loads(path.read_text(encoding="utf-8"))
    normalized: list[tuple[str, str | None, str, str | None, str, str]] = []
    seen_ids: set[str] = set()
    for item in chunks:
        chunk_id = str(item.get("chunkId", "")).strip()
        if not chunk_id:
            continue
        if chunk_id in seen_ids:
            raise ValueError(f"Duplicate scenic knowledge chunk id: {chunk_id}")
        seen_ids.add(chunk_id)
        title = str(item.get("title", chunk_id)).strip() or chunk_id
        content = str(item.get("content", "")).strip()
        if not content:
            raise ValueError(f"Scenic knowledge chunk has no content: {chunk_id}")
        normalized.append(
            (
                chunk_id,
                item.get("spotId"),
                title,
                item.get("topic"),
                str(item.get("source", "景区资料")),
                content,
            )
        )

    with database() as connection:
        old_ids = [
            row["chunk_id"]
            for row in connection.execute("SELECT chunk_id FROM kb_chunks WHERE doc_id IS NULL")
        ]
        _delete_fts(connection, old_ids)
        connection.execute("DELETE FROM kb_chunks WHERE doc_id IS NULL")
        created_at = int(time())
        for chunk_id, spot_id, title, topic, source, content in normalized:
            connection.execute(
                """
                INSERT INTO kb_chunks (chunk_id, spot_id, title, topic, source, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, spot_id, title, topic, source, content, created_at),
            )
            connection.execute(
                "INSERT INTO kb_chunks_fts (chunk_id, title, content, source) VALUES (?, ?, ?, ?)",
                (chunk_id, title, content, source),
            )


def search_knowledge(query: str, limit: int = 5, spot_id: str = "") -> list[dict]:
    clean = query.strip()
    if not clean:
        raise ValueError("Query is empty")
    bounded = max(1, min(limit, 20))
    with database() as connection:
        if len(clean) >= 3:
            try:
                rows = connection.execute(
                    """
                    SELECT c.chunk_id, c.title, c.source, c.content, bm25(kb_chunks_fts) AS rank
                    FROM kb_chunks_fts
                    JOIN kb_chunks c ON c.chunk_id = kb_chunks_fts.chunk_id
                    WHERE kb_chunks_fts MATCH ?
                    ORDER BY rank LIMIT ?
                    """,
                    (f'"{clean.replace(chr(34), chr(34) * 2)}"', bounded),
                ).fetchall()
            except Exception:
                rows = []
        else:
            rows = connection.execute(
                """
                SELECT chunk_id, title, source, content, 0.0 AS rank FROM kb_chunks
                WHERE title LIKE ? OR content LIKE ? LIMIT ?
                """,
                (f"%{clean}%", f"%{clean}%", bounded),
            ).fetchall()
        # Natural-language questions often do not exactly match an FTS phrase.
        # Current-spot material is a grounded fallback, never a fabricated citation.
        if not rows and spot_id:
            rows = connection.execute(
                """
                SELECT chunk_id, title, source, content, 0.0 AS rank
                FROM kb_chunks WHERE spot_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (spot_id, bounded),
            ).fetchall()
        if not rows:
            rows = connection.execute(
                """
                SELECT chunk_id, title, source, content, 0.0 AS rank
                FROM kb_chunks
                WHERE title LIKE ? OR content LIKE ? LIMIT ?
                """,
                (f"%{clean[:24]}%", f"%{clean[:24]}%", bounded),
            ).fetchall()
    return [
        {
            "title": row["title"],
            "chunkId": row["chunk_id"],
            "source": row["source"],
            "score": round(1 / (1 + abs(float(row["rank"]))), 3),
            "contentPreview": row["content"][:200],
        }
        for row in rows
    ]
