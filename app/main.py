import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.ai import router as ai_router
from app.api.audio import router as audio_router
from app.api.dashboard import router as dashboard_router
from app.api.feedback import router as feedback_router
from app.api.kb import router as kb_router
from app.api.map import router as map_router
from app.api.messages import router as messages_router
from app.api.recommend import router as recommend_router
from app.api.rooms import router as rooms_router
from app.api.routes import router as routes_router
from app.api.spots import router as spots_router
from app.api.users import router as users_router
from app.api.vision import router as vision_router
from app.core.config import settings
from app.core.database import database_ready, initialize_database
from app.core.errors import AppError
from app.core.logging import request_id_var, setup_logging
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security import SecurityMiddleware
from app.services.knowledge import seed_scenic_chunks
from app.services.users import cleanup_auth_state, ensure_bootstrap_admin

for directory in ["uploads", "uploads/tts", "uploads/audio", "uploads/kb", "data"]:
    Path(directory).mkdir(parents=True, exist_ok=True)

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


def _cleanup_partial_uploads() -> None:
    for directory in (Path("uploads/audio"), Path("uploads/kb")):
        for path in directory.glob("*.part"):
            path.unlink(missing_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    ensure_bootstrap_admin()
    seed_scenic_chunks()
    _cleanup_partial_uploads()

    async def cleanup_loop() -> None:
        while True:
            await asyncio.sleep(300)
            cleanup_auth_state()
            _cleanup_partial_uploads()

    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="A5 Intelligent Tour Guide System", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(rooms_router)
app.include_router(messages_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(audio_router)
app.include_router(vision_router)
app.include_router(recommend_router)
app.include_router(spots_router)
app.include_router(routes_router)
app.include_router(kb_router)
app.include_router(map_router)
app.include_router(dashboard_router)
app.include_router(feedback_router)

frontend_root = Path("frontend-v4")
if frontend_root.exists():
    app.mount("/assets", StaticFiles(directory=frontend_root / "assets"), name="frontend-assets")
    app.mount("/pages", StaticFiles(directory=frontend_root / "pages", html=True), name="frontend-pages")
    app.mount("/frontend-v4", StaticFiles(directory=frontend_root, html=True), name="frontend-v4")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def _error_response(request: Request, status: int, detail: str, code: str, headers=None):
    return JSONResponse(
        status_code=status,
        headers=headers,
        content={
            "detail": detail,
            "errorCode": code,
            "requestId": request_id_var.get(""),
        },
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return _error_response(request, exc.status_code, str(exc.detail), exc.error_code, exc.headers)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return _error_response(
        request,
        exc.status_code,
        str(exc.detail),
        f"HTTP_{exc.status_code}",
        exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return _error_response(request, 422, "Request validation failed", "VALIDATION_ERROR")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning("ValueError at %s %s: %s", request.method, request.url.path, exc)
    return _error_response(request, 422, str(exc), "INVALID_PARAMETER")


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError):
    logger.warning("Timeout at %s %s: %s", request.method, request.url.path, exc)
    return _error_response(request, 504, "Request timed out, please retry.", "TIMEOUT")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception at %s %s: %s", request.method, request.url.path, exc)
    return _error_response(request, 500, "Internal server error, please retry later.", "INTERNAL_ERROR")


@app.get("/health/live")
async def live():
    return {"status": "live"}


@app.get("/health/ready")
async def ready():
    if not database_ready():
        raise AppError(503, "DATABASE_UNAVAILABLE", "Database is not ready")
    return {"status": "ready", "database": "ok", "workerMode": "single"}


@app.get("/")
async def root():
    return {
        "service": "A5 Intelligent Tour Guide System",
        "version": "2.0.0",
        "status": "running",
        "frontendApiPrefix": "/api",
        "algorithmInternalPrefix": "/v1",
        "features": {
            "asr": settings.enable_asr,
            "tts": settings.enable_tts,
            "vision": settings.enable_vision,
            "rag": settings.enable_rag,
            "persistence": "sqlite",
            "realtime": "single-worker",
            "llmMode": "provider" if settings.llm_enabled else "mock",
            "visionMode": "provider" if settings.vision_enabled else "mock",
            "audioMode": "provider" if settings.audio_provider_enabled else "mock",
            "mapMode": "amap" if settings.map_enabled and settings.map_provider == "amap" else "disabled",
        },
    }


# 前端与 API 同源提供，确保浏览器只访问一个 8000 端口。
# 必须放在所有 API/健康检查路由之后，避免根路径静态挂载遮挡接口。
frontend_dir = Path("frontend-v4")
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
