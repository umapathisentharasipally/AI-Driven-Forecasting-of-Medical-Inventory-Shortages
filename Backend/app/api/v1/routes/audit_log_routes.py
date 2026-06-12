from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import AUDIT_READ
from app.core.response_handler import paginated_response
from app.core.role_checker import RoleChecker
from app.schemas.audit_log_schema import AuditLogFilter
from app.services import audit_log_service

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    user_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([AUDIT_READ])),
):
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    logs, total = await audit_log_service.get_logs(db, filters)

    return paginated_response(
        data=[log.model_dump(mode="json") for log in logs],
        total=total,
        page=page,
        limit=limit,
        message="Audit logs fetched successfully",
    )


@router.get("/user/{user_id}")
async def get_logs_by_user(
    user_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([AUDIT_READ])),
):
    logs, total = await audit_log_service.get_logs_by_user(
        db=db,
        user_id=user_id,
        page=page,
        limit=limit,
    )

    return paginated_response(
        data=[log.model_dump(mode="json") for log in logs],
        total=total,
        page=page,
        limit=limit,
        message="User audit logs fetched successfully",
    )


@router.get("/resource/{type}/{id}")
async def get_logs_by_resource(
    type: str,
    id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([AUDIT_READ])),
):
    logs, total = await audit_log_service.get_logs_by_resource(
        db=db,
        resource_type=type,
        resource_id=id,
        page=page,
        limit=limit,
    )

    return paginated_response(
        data=[log.model_dump(mode="json") for log in logs],
        total=total,
        page=page,
        limit=limit,
        message="Resource audit logs fetched successfully",
    )