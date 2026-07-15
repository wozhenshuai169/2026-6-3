from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.logging import request_id_var


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        try:
            too_large = bool(content_length) and int(content_length) > settings.max_request_bytes
        except ValueError:
            too_large = True
        if not content_length:
            body = await request.body()
            too_large = len(body) > settings.max_request_bytes
        if too_large:
            response = JSONResponse(
                status_code=413,
                content={
                    "detail": "Request body is too large.",
                    "errorCode": "REQUEST_TOO_LARGE",
                    "requestId": request_id_var.get(""),
                },
            )
            self._add_headers(response)
            return response
        response = await call_next(request)
        self._add_headers(response)
        return response

    @staticmethod
    def _add_headers(response: Response) -> None:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
