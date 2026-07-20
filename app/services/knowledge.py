import json
import re
from io import BytesIO
from pathlib import Path
from time import time
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from app.core.database import database

DATA_DIR = Path("data")
UPLOAD_DIR = Path("uploads") / "kb"
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
SHEET_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _extract_docx_text(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError("Invalid DOCX document") from exc
    paragraphs = []
    for node in root.findall(".//w:p", WORD_NS):
        text = "".join(item.text or "" for item in node.findall(".//w:t", WORD_NS)).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _extract_xlsx_schema(content: bytes) -> str:
    """Index workbook structure only; raw visitor rows must not enter the RAG corpus."""
    try:
        with ZipFile(BytesIO(content)) as archive:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    except (BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError("Invalid XLSX workbook") from exc
    names = [sheet.attrib.get("name", "未命名工作表") for sheet in workbook.findall(".//x:sheets/x:sheet", SHEET_NS)]
    if not names:
        raise ValueError("Workbook does not contain a worksheet")
    return (
        f"工作簿包含工作表：{'、'.join(names)}。"
        "为保护游客隐私，原始表格行数据不会写入问答知识库；"
        "请通过数据聚合任务生成脱敏的景点级运营洞察后再用于后台分析。"
    )


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
    if suffix == ".docx":
        return _extract_docx_text(content)
    if suffix == ".xlsx":
        return _extract_xlsx_schema(content)
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
    # Time-bounded operational notices must take precedence over archived facts.
    from app.services.operation_events import active_event_chunks

    realtime = active_event_chunks(clean)
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
        if not rows:
            rows = _phrase_fallback(connection, clean, bounded)
    archived = [
        {
            "title": row["title"],
            "chunkId": row["chunk_id"],
            "source": row["source"],
            "score": round(1 / (1 + abs(float(row["rank"]))), 3),
            "contentPreview": row["content"][:200],
        }
        for row in rows
    ]
    return (realtime + archived)[:bounded]


def _phrase_fallback(connection, query: str, limit: int):
    """Rank Chinese phrase overlap when FTS cannot match a whole spoken question."""
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", query)
    if len(normalized) < 2:
        return []
    phrases = {
        normalized[index : index + width]
        for width in range(min(8, len(normalized)), 1, -1)
        for index in range(len(normalized) - width + 1)
    }
    candidates = connection.execute(
        "SELECT chunk_id, title, source, content, 0.0 AS rank FROM kb_chunks"
    ).fetchall()
    scored = []
    for row in candidates:
        title, content = str(row["title"]), str(row["content"])
        matches = [phrase for phrase in phrases if phrase in title or phrase in content]
        if not matches:
            continue
        score = max(len(phrase) for phrase in matches)
        score += sum(0.1 for phrase in matches if len(phrase) >= 3)
        if any(phrase in title for phrase in matches):
            score += 0.5
        scored.append((score, row))
    return [row for _, row in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]
