"""
Middleware — Rate Limiting & Request Logging
--------------------------------------------
In-memory sliding window rate limiter (no external dependencies).
Logs every incoming request with method, path, status, and latency.
"""

import logging
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("arenamind.middleware")


# ---------------------------------------------------------------------------
# Request Logging Middleware
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing info."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} "
            f"({duration_ms}ms) "
            f"[{request.client.host if request.client else 'unknown'}]"
        )
        # Inject timing header
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response


# ---------------------------------------------------------------------------
# In-Memory Sliding Window Rate Limiter
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter keyed by client IP.

    Config:
        max_requests: Max allowed requests per window.
        window_seconds: Rolling window duration in seconds.
        exempt_paths: Paths that bypass rate limiting (e.g. /health).
    """

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 120,
        window_seconds: int = 60,
        exempt_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exempt_paths = set(exempt_paths or ["/health", "/docs", "/openapi.json", "/redoc"])
        # {ip: deque of timestamps}
        self._windows: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Exempt certain paths
        if path in self.exempt_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "anonymous"
        now = time.time()
        window = self._windows[client_ip]

        # Evict timestamps older than the window
        while window and window[0] < now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            logger.warning(
                f"[RATE_LIMIT] IP {client_ip} exceeded {self.max_requests} "
                f"requests/{self.window_seconds}s on {path}"
            )
            return Response(
                content='{"status_code":429,"error":"RATE_LIMIT_EXCEEDED",'
                        '"message":"Too many requests. Please slow down."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        window.append(now)
        response = await call_next(request)

        remaining = self.max_requests - len(window)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ---------------------------------------------------------------------------
# Registration Helper
# ---------------------------------------------------------------------------

def register_middleware(app: FastAPI) -> None:
    """Attach all middleware to the FastAPI app (order matters — last added = outermost)."""
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=120,
        window_seconds=60,
    )
    app.add_middleware(RequestLoggingMiddleware)
