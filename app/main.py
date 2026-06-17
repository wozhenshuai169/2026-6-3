import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.ai import router as ai_router
from app.api.audio import router as audio_router
from app.api.dashboard import router as dashboard_router
from app.api.feedback import router as feedback_router
from app.api.kb import router as kb_router
from app.api.recommend import router as recommend_router
from app.api.rooms import router as rooms_router
from app.api.routes import router as routes_router
from app.api.spots import router as spots_router
from app.api.users import router as users_router
from app.api.vision import router as vision_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.logging import RequestLoggingMiddleware

for directory in ["uploads", "uploads/tts", "uploads/audio", "uploads/kb", "data"]:
    Path(directory).mkdir(parents=True, exist_ok=True)

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="A5 Intelligent Tour Guide System", version="1.0.0")
app.add_middleware(RequestLoggingMiddleware)

app.include_router(rooms_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(audio_router)
app.include_router(vision_router)
app.include_router(recommend_router)
app.include_router(spots_router)
app.include_router(routes_router)
app.include_router(kb_router)
app.include_router(dashboard_router)
app.include_router(feedback_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend-v4 at root
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend-v4"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning("ValueError at %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "errorCode": "INVALID_PARAMETER"},
    )


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError):
    logger.warning("Timeout at %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=504,
        content={"detail": "Request timed out, please retry.", "errorCode": "TIMEOUT"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception at %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error, please retry later.", "errorCode": "INTERNAL_ERROR"},
    )


@app.get("/")
async def root():
    return {
        "service": "A5 Intelligent Tour Guide System",
        "version": "1.0.0",
        "status": "running",
        "frontendApiPrefix": "/api",
        "algorithmInternalPrefix": "/v1",
        "features": {
            "asr": settings.enable_asr,
            "tts": settings.enable_tts,
            "vision": settings.enable_vision,
            "rag": settings.enable_rag,
        },
    }
