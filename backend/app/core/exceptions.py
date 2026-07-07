"""
Custom Exceptions & Global Exception Handlers
----------------------------------------------
Centralizes all error handling so every exception returns a structured
JSON envelope: { "error": <code>, "message": <detail>, "status_code": <n> }
"""

import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger("arenamind.exceptions")


# ---------------------------------------------------------------------------
# Standard Error Response Helper
# ---------------------------------------------------------------------------

def error_response(status_code: int, error: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "error": error,
            "message": message,
        },
    )


# ---------------------------------------------------------------------------
# Custom Domain Exceptions
# ---------------------------------------------------------------------------

class ArenaMindException(Exception):
    """Base exception for all ArenaMind business logic errors."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class NotFoundError(ArenaMindException):
    def __init__(self, resource: str, resource_id: str = ""):
        detail = f"{resource} not found" + (f": {resource_id}" if resource_id else "")
        super().__init__(detail, status.HTTP_404_NOT_FOUND, "NOT_FOUND")


class UnauthorizedError(ArenaMindException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")


class ForbiddenError(ArenaMindException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


class ConflictError(ArenaMindException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT, "CONFLICT")


class RateLimitError(ArenaMindException):
    def __init__(self):
        super().__init__(
            "Rate limit exceeded. Please slow down your requests.",
            status.HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMIT_EXCEEDED",
        )


# ---------------------------------------------------------------------------
# Exception Handler Registration
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app."""

    @app.exception_handler(ArenaMindException)
    async def arenamind_exception_handler(request: Request, exc: ArenaMindException):
        logger.error(f"[{exc.error_code}] {exc.message} — {request.method} {request.url}")
        return error_response(exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"[HTTP {exc.status_code}] {exc.detail} — {request.method} {request.url}")
        return error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            field = " → ".join(str(loc) for loc in err["loc"])
            errors.append(f"{field}: {err['msg']}")
        message = "; ".join(errors)
        logger.warning(f"[VALIDATION_ERROR] {message} — {request.method} {request.url}")
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            message,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(f"[UNHANDLED] {type(exc).__name__}: {exc} — {request.method} {request.url}")
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred. Our team has been notified.",
        )
