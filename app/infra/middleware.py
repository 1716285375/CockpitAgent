import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infra.logger import logger
from app.infra.metrics import MetricsRegistry


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, metrics: MetricsRegistry | None = None):
        super().__init__(app)
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        if self.metrics is not None:
            self.metrics.increment(
                "http_requests_total",
                method=request.method,
                path=request.url.path,
                status=str(response.status_code),
            )
        logger.info(
            "request completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
