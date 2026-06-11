import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.logger import get_logger

logger = get_logger(__name__)

WRITE_METHODS = {"POST", "PATCH", "DELETE"}


async def audit_stub(method: str, path: str, user_id: str | None, status_code: int) -> None:
    logger.info(
        "audit_event",
        method=method,
        path=path,
        user_id=user_id,
        status_code=status_code,
    )


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method in WRITE_METHODS and response.status_code < 400:
            user_id = getattr(request.state, "user_id", None)
            asyncio.create_task(
                audit_stub(
                    method=request.method,
                    path=request.url.path,
                    user_id=user_id,
                    status_code=response.status_code,
                )
            )

        return response