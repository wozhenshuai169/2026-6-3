"""请求日志中间件 —— 注入 request_id，记录请求/响应。"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import (
    generate_request_id,
    set_request_context,
    request_id_var,
    current_endpoint_var,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """为每个请求注入 request_id，记录耗时和状态码。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_context(rid, request.url.path)

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = rid
        logger.info(
            "%s %s -> %d (%.0fms)",
            request.method, request.url.path, response.status_code, elapsed,
        )
        return response
