import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.rooms import router as rooms_router
from app.api.ai import router as ai_router
from app.api.users import router as users_router
from app.api.audio import router as audio_router
from app.api.vision import router as vision_router
from app.api.recommend import router as recommend_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.logging import RequestLoggingMiddleware

# ── 初始化日志 ──────────────────────────────────
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="A5 智能导游系统", version="1.0.0")

# ── 中间件 ─────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

# ── 路由 ───────────────────────────────────────
app.include_router(rooms_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(audio_router)
app.include_router(vision_router)
app.include_router(recommend_router)

# ── 静态文件 ───────────────────────────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ═══════════════════════════════════════════════════
# 全局异常兜底
# ═══════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底异常处理 —— 记录日志并返回统一错误格式。"""
    logger.exception(
        "Unhandled exception at %s %s: %s",
        request.method, request.url.path, exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误，请稍后重试。",
            "errorCode": "INTERNAL_ERROR",
        },
    )


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
        content={"detail": "请求超时，请重试。", "errorCode": "TIMEOUT"},
    )


# ═══════════════════════════════════════════════════
# 根路径
# ═══════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "A5 智能导游系统",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "asr": settings.enable_asr,
            "tts": settings.enable_tts,
            "vision": settings.enable_vision,
            "rag": settings.enable_rag,
        },
    }
