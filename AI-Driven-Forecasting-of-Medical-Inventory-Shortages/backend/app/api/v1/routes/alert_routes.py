from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import ALERT_READ, ALERT_WRITE
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.alert_schema import AlertAssignRequest, AlertFilter, AlertStatusUpdate
from app.services import alert_service

router = APIRouter()


@router.get("/")
async def list_alerts(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    alert_type: Optional[str] = Query(default=None),
    item_id: Optional[str] = Query(default=None),
    facility_id: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_READ])),
):
    filters = AlertFilter(
        status=status,
        severity=severity,
        alert_type=alert_type,
        item_id=item_id,
        facility_id=facility_id,
        assigned_to=assigned_to,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    alerts, total = await alert_service.get_alerts(db, filters)

    return paginated_response(
        data=[alert.model_dump(mode="json") for alert in alerts],
        total=total,
        page=page,
        limit=limit,
        message="Alerts fetched successfully",
    )


@router.get("/dashboard/counts")
async def dashboard_counts(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_READ])),
):
    counts = await alert_service.get_dashboard_counts(db)

    return success_response(
        data=counts.model_dump(mode="json"),
        message="Alert dashboard counts fetched successfully",
    )


@router.get("/{id}")
async def get_alert(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_READ])),
):
    alert = await alert_service.get_alert(db, id)

    return success_response(
        data=alert.model_dump(mode="json"),
        message="Alert fetched successfully",
    )


@router.patch("/{id}/status")
async def update_status(
    id: str,
    data: AlertStatusUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_WRITE])),
):
    alert = await alert_service.update_status(
        db=db,
        id=id,
        data=data,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=alert.model_dump(mode="json"),
        message="Alert status updated successfully",
    )


@router.patch("/{id}/assign")
async def assign_alert(
    id: str,
    data: AlertAssignRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_WRITE])),
):
    alert = await alert_service.assign_alert(db, id, data)

    return success_response(
        data=alert.model_dump(mode="json"),
        message="Alert assigned successfully",
    )