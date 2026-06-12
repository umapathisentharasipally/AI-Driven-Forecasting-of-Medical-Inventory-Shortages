from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)

SKIP_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _should_skip(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in SKIP_PREFIXES)


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if _should_skip(request.url.path):
            return await call_next(request)

        start = utc_now()
        response = None

        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((utc_now() - start).total_seconds() * 1000, 2)

            user = getattr(request.state, "user", None)
            user_id = str(user["_id"]) if user else None

            logger.bind(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code if response else 500,
                duration_ms=duration_ms,
                user_id=user_id,
                ip=_client_ip(request),
            ).info("request_completed")