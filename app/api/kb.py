import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field

from app.core.auth import require_roles
from app.core.errors import AppError
from app.core.rate_limit import enforce_rate_limit
from app.services.knowledge import (
    UPLOAD_DIR,
    create_document,
    delete_document,
    get_document,
    list_documents,
    rebuild_index,
    search_knowledge,
)

router = APIRouter(prefix="/api/kb")
ALLOWED_SUFFIXES = {".txt", ".md", ".json", ".pdf", ".docx", ".xlsx"}
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_MIME = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".json": {"application/json", "text/json", "text/plain"},
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
}


class TestQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


def _safe_filename(filename: str) -> tuple[str, str]:
    display = filename.replace("\\", "/").split("/")[-1]
    suffix = Path(display).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(display).stem).strip("._")[:50] or "doc"
    return display, f"{stem}_{uuid4().hex[:8]}{suffix}"


@router.post("/upload")
async def upload_doc(
    file: UploadFile = File(...),
    admin: dict = Depends(require_roles("admin")),
):
    enforce_rate_limit("upload", admin["userId"], 10, 600)
    display_name, safe_name = _safe_filename(file.filename or "doc")
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise AppError(415, "UNSUPPORTED_DOCUMENT", "Unsupported file type")
    if file.content_type not in ALLOWED_MIME[suffix]:
        raise AppError(415, "INVALID_DOCUMENT_MIME", "Document MIME type is not allowed")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    final_path = UPLOAD_DIR / safe_name
    temp_path = final_path.with_suffix(final_path.suffix + ".part")
    total = 0
    try:
        with temp_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_FILE_SIZE:
                    raise AppError(413, "DOCUMENT_TOO_LARGE", "File is too large")
                output.write(chunk)
        if suffix == ".pdf" and not temp_path.read_bytes()[:5].startswith(b"%PDF-"):
            raise AppError(415, "INVALID_DOCUMENT", "PDF signature is invalid")
        if suffix in {".docx", ".xlsx"} and not temp_path.read_bytes()[:2].startswith(b"PK"):
            raise AppError(415, "INVALID_DOCUMENT", "Office document signature is invalid")
        temp_path.replace(final_path)
        try:
            return create_document(display_name, safe_name, suffix, total)
        except Exception as exc:
            final_path.unlink(missing_ok=True)
            raise AppError(422, "DOCUMENT_INDEX_FAILED", str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)
        await file.close()


@router.get("/docs")
async def docs(admin: dict = Depends(require_roles("admin"))):
    del admin
    return {"docs": list_documents()}


@router.get("/docs/{docId}")
async def doc_detail(docId: str, admin: dict = Depends(require_roles("admin"))):
    del admin
    try:
        return get_document(docId)
    except KeyError as exc:
        raise AppError(404, "DOCUMENT_NOT_FOUND", "Document not found") from exc


@router.delete("/docs/{docId}", status_code=204)
async def remove_doc(docId: str, admin: dict = Depends(require_roles("admin"))):
    del admin
    try:
        delete_document(docId)
    except KeyError as exc:
        raise AppError(404, "DOCUMENT_NOT_FOUND", "Document not found") from exc


@router.post("/rebuild")
async def rebuild(admin: dict = Depends(require_roles("admin"))):
    del admin
    return rebuild_index()


@router.post("/test-query")
async def test_query(req: TestQueryRequest, admin: dict = Depends(require_roles("admin"))):
    del admin
    return {"query": req.query.strip(), "results": search_knowledge(req.query, req.limit)}
