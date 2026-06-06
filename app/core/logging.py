"""结构化日志配置 —— 统一格式、请求ID追踪、耗时统计。"""

import logging
import sys
import time
import uuid
from contextvars import ContextVar

# ── 请求级上下文 ────────────────────────────────
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
current_endpoint_var: ContextVar[str] = ContextVar("endpoint", default="")


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


def set_request_context(request_id: str, endpoint: str = "") -> None:
    request_id_var.set(request_id)
    current_endpoint_var.set(endpoint)


def get_request_id() -> str:
    return request_id_var.get()


# ── 日志格式 ────────────────────────────────────

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-7s | "
    "[%(name)s] | %(message)s"
)

STRUCTURED_FORMAT = (
    "%(asctime)s | %(levelname)-7s | rid=%(rid)s | ep=%(ep)s | "
    "[%(name)s] | %(message)s"
)


class RequestIDFilter(logging.Filter):
    """将 ContextVar 注入日志 record。"""
    def filter(self, record: logging.LogRecord) -> bool:
        record.rid = request_id_var.get() or "-"
        record.ep = current_endpoint_var.get() or "-"
        return True


def setup_logging(level: str = "INFO") -> None:
    """初始化全局日志配置。"""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除已有 handler
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 使用结构化格式
    formatter = logging.Formatter(STRUCTURED_FORMAT, datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root.addHandler(handler)

    # 抑制 httpx / uvicorn 的 DEBUG 噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# ── 耗时记录器 ──────────────────────────────────

class Timer:
    """上下文管理器：记录代码块耗时。"""
    def __init__(self, logger: logging.Logger, label: str):
        self._logger = logger
        self._label = label
        self._start = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = (time.perf_counter() - self._start) * 1000
        self._logger.info("%s took %.0fms", self._label, elapsed)

    @property
    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000


def log_model_call(logger: logging.Logger, model: str, ms: float, token_count: int = 0,
                   success: bool = True, error: str = "") -> None:
    """记录一次模型调用的结构化日志。"""
    status = "OK" if success else "FAIL"
    extra = f"tokens={token_count}" if token_count else ""
    err = f" err={error}" if error else ""
    logger.info("model_call | model=%-20s | %4.0fms | %s%s%s",
                model, ms, status, f" {extra}" if extra else "", err)
