import json
import re
from pathlib import Path
from time import time
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api/kb")

DATA_DIR = Path("data")
UPLOAD_DIR = Path("uploads") / "kb"
DOCS_PATH = DATA_DIR / "kb_docs.json"
ALLOWED_SUFFIXES = {".txt", ".md", ".json", ".pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024


class TestQueryRequest(BaseModel):
    query: str
    limit: int = 5


def _safe_filename(filename: str) -> str:
    display_name = filename.replace("\\", "/").split("/")[-1]
    stem = Path(display_name).stem
    suffix = Path(display_name).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._")[:50] or "doc"
    return f"{safe_stem}_{uuid4().hex[:8]}{suffix}"


def _display_filename(filename: str | None) -> str:
    return (filename or "doc").replace("\\", "/").split("/")[-1]


def _load_docs() -> list[dict]:
    if not DOCS_PATH.exists():
        return []
    return json.loads(DOCS_PATH.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    try:
        tmp_path.replace(path)
    except PermissionError:
        path.write_text(payload, encoding="utf-8")
        try:
            tmp_path.unlink(missing_ok=True)
        except PermissionError:
            pass


def _load_chunks() -> list[dict]:
    path = DATA_DIR / "scenic_chunks.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _score_text(query: str, text: str) -> float:
    terms = [term for term in re.split(r"\s+", query.strip().lower()) if term]
    if not terms:
        terms = list(query.strip().lower())
    haystack = text.lower()
    hits = sum(1 for term in terms if term and term in haystack)
    return round(hits / max(len(terms), 1), 3)


@router.post("/upload")
async def upload_doc(file: UploadFile = File(...)):
    display_name = _display_filename(file.filename)
    suffix = Path(display_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    safe_name = _safe_filename(display_name or f"doc{suffix}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / safe_name
    file_path.write_bytes(content)

    docs = _load_docs()
    doc = {
        "docId": uuid4().hex,
        "originalName": display_name,
        "fileName": safe_name,
        "fileUrl": f"/uploads/kb/{safe_name}",
        "suffix": suffix,
        "size": len(content),
        "uploadedAt": int(time()),
        "status": "uploaded",
    }
    docs.append(doc)
    _atomic_write_json(DOCS_PATH, docs)
    return doc


@router.get("/docs")
async def list_docs():
    return {"docs": _load_docs()}


@router.post("/rebuild")
async def rebuild_kb():
    docs = _load_docs()
    for doc in docs:
        doc["status"] = "indexed"
        doc["indexedAt"] = int(time())
    _atomic_write_json(DOCS_PATH, docs)
    return {
        "status": "rebuilt",
        "docCount": len(docs),
        "message": "Knowledge search cache refreshed; keyword search is active.",
    }


@router.post("/test-query")
async def test_query(req: TestQueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")

    results = []
    for chunk in _load_chunks():
        text = " ".join(str(chunk.get(key, "")) for key in ["title", "topic", "content", "source"])
        score = _score_text(query, text)
        if score > 0:
            results.append(
                {
                    "title": chunk.get("title"),
                    "chunkId": chunk.get("chunkId"),
                    "score": score,
                    "contentPreview": str(chunk.get("content", ""))[:160],
                }
            )

    for doc in _load_docs():
        path = UPLOAD_DIR / doc.get("fileName", "")
        text = ""
        if path.suffix.lower() in {".txt", ".md", ".json"} and path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
        score = _score_text(query, f"{doc.get('originalName', '')} {text}")
        if score > 0:
            results.append(
                {
                    "title": doc.get("originalName"),
                    "chunkId": doc.get("docId"),
                    "score": score,
                    "contentPreview": text[:160],
                }
            )

    results.sort(key=lambda item: item["score"], reverse=True)
    return {"query": query, "results": results[: max(1, req.limit)]}
