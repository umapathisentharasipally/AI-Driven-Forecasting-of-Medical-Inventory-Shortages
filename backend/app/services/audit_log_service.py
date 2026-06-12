from typing import List, Tuple

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import audit_log_repository
from app.schemas.audit_log_schema import AuditLogFilter, AuditLogResponse
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger
from app.utils.validation_utils import validate_pagination

logger = get_logger(__name__)


def to_audit_log_response(log: dict) -> AuditLogResponse:
    return AuditLogResponse(
        id=str(log["_id"]),
        user_id=log.get("user_id"),
        action=log["action"],
        resource_type=log["resource_type"],
        resource_id=log.get("resource_id"),
        changes=log.get("changes"),
        ip_address=log.get("ip_address"),
        user_agent=log.get("user_agent"),
        created_at=log["created_at"],
    )


async def log_action(
    db: AsyncIOMotorDatabase,
    user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    changes: dict | None = None,
    request: Request | None = None,
) -> None:
    try:
        ip_address = None
        user_agent = None

        if request is not None:
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                ip_address = forwarded_for.split(",")[0].strip()
            elif request.client:
                ip_address = request.client.host

            user_agent = request.headers.get("user-agent")

        log_doc = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "changes": changes,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": utc_now(),
        }

        await audit_log_repository.create(db, log_doc)

    except Exception as exc:
        logger.error(f"audit_log_service.log_action failed: {exc}")


async def get_logs(
    db: AsyncIOMotorDatabase,
    filters: AuditLogFilter,
) -> Tuple[List[AuditLogResponse], int]:
    page, limit = validate_pagination(filters.page, filters.limit)

    logs, total = await audit_log_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters=filters.model_dump(exclude_none=True),
    )

    return [to_audit_log_response(log) for log in logs], total


async def get_logs_by_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    page: int,
    limit: int,
) -> Tuple[List[AuditLogResponse], int]:
    page, limit = validate_pagination(page, limit)

    logs, total = await audit_log_repository.get_by_user(
        db=db,
        user_id=user_id,
        page=page,
        limit=limit,
    )

    return [to_audit_log_response(log) for log in logs], total


async def get_logs_by_resource(
    db: AsyncIOMotorDatabase,
    resource_type: str,
    resource_id: str,
    page: int,
    limit: int,
) -> Tuple[List[AuditLogResponse], int]:
    page, limit = validate_pagination(page, limit)

    logs, total = await audit_log_repository.get_by_resource(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        limit=limit,
    )

    return [to_audit_log_response(log) for log in logs], total