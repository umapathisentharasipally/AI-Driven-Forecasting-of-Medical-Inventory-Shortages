from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Any] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(404, "NOT_FOUND", message, details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", details: Any = None):
        super().__init__(401, "UNAUTHORIZED", message, details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", details: Any = None):
        super().__init__(403, "FORBIDDEN", message, details)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", details: Any = None):
        super().__init__(409, "CONFLICT", message, details)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", details: Any = None):
        super().__init__(422, "VALIDATION_ERROR", message, details)


class MLInferenceException(AppException):
    def __init__(self, message: str = "ML inference failed", details: Any = None):
        super().__init__(503, "ML_INFERENCE_ERROR", message, details)


class DatabaseException(AppException):
    def __init__(self, message: str = "Database error", details: Any = None):
        super().__init__(500, "DB_ERROR", message, details)


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "timestamp": utc_now().isoformat(),
    }
    return JSONResponse(status_code=status_code, content=payload)


async def app_exception_handler(request: Request, exc: AppException):
    return error_response(exc.status_code, exc.error_code, exc.message, exc.details)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = exc.errors() if settings.APP_ENV == "development" else None
    return error_response(422, "REQUEST_VALIDATION_ERROR", "Invalid request payload", details)


async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(exc.status_code, "HTTP_ERROR", str(exc.detail), None)


async def fallback_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")

    details = str(exc) if settings.APP_ENV == "development" else None
    message = (
        "Internal server error"
        if settings.APP_ENV != "development"
        else "Unhandled internal exception"
    )

    return error_response(500, "INTERNAL_SERVER_ERROR", message, details)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(NotFoundException, app_exception_handler)
    app.add_exception_handler(UnauthorizedException, app_exception_handler)
    app.add_exception_handler(ForbiddenException, app_exception_handler)
    app.add_exception_handler(ConflictException, app_exception_handler)
    app.add_exception_handler(ValidationException, app_exception_handler)
    app.add_exception_handler(MLInferenceException, app_exception_handler)
    app.add_exception_handler(DatabaseException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, fallback_exception_handler)