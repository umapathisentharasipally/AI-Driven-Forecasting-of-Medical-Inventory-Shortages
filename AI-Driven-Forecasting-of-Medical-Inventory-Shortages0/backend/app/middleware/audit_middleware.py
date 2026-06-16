import asyncio

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config.database import get_database
from app.services.audit_log_service import log_action
from app.utils.logger import get_logger

logger = get_logger(__name__)

WRITE_METHODS = {"POST", "PATCH", "DELETE"}
SKIP_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
)


def _should_skip(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in SKIP_PREFIXES)


def _infer_resource_type(path: str) -> str:
    parts = [part for part in path.split("/") if part]

    mapping = {
        "users": "user",
        "roles": "role",
        "inventory": "inventory_item",
        "vendors": "vendor",
        "alerts": "alert",
        "notifications": "notification",
        "reports": "report",
        "predictions": "prediction",
        "anomalies": "anomaly",
        "trends": "trend",
        "uploads": "inventory_item",
        "upload": "inventory_item",
        "export": "report",
        "exports": "report",
        "audit-logs": "audit_log",
    }

    for part in parts:
        if part in mapping:
            return mapping[part]

    return "unknown"


def _infer_action(method: str, path: str) -> str:
    lowered = path.lower()

    if "/stock" in lowered:
        return "STOCK_ADJUST"

    if "/batch" in lowered:
        return "BATCH_PREDICT"

    if "/export" in lowered or "/exports" in lowered:
        return "EXPORT"

    if "change-password" in lowered:
        return "PASSWORD_CHANGE"

    if method == "POST":
        return "CREATE"

    if method == "PATCH":
        return "UPDATE"

    if method == "DELETE":
        return "DELETE"

    return "UNKNOWN"


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if (
            request.method in WRITE_METHODS
            and response.status_code < 400
            and not _should_skip(request.url.path)
        ):
            try:
                user = getattr(request.state, "user", None)

                if user:
                    db = await get_database()

                    asyncio.create_task(
                        log_action(
                            db=db,
                            user_id=str(user["_id"]),
                            action=_infer_action(request.method, request.url.path),
                            resource_type=_infer_resource_type(request.url.path),
                            resource_id=None,
                            changes=None,
                            request=request,
                        )
                    )

            except Exception as exc:
                logger.error(f"Audit middleware scheduling failed: {exc}")

        return response