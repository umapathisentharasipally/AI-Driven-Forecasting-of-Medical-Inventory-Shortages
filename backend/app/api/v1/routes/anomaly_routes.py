from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import ALERT_WRITE, PREDICTION_READ, PREDICTION_RUN
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.anomaly_schema import AnomalyAcknowledgeRequest, AnomalyFilter
from app.services import anomaly_service

router = APIRouter()


@router.post("/detect")
async def detect_anomalies(
    facility_id: Optional[str] = Query(default=None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_RUN])),
):
    result = await anomaly_service.detect_for_all(
        db=db,
        facility_id=facility_id,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=result,
        message="Anomaly detection completed successfully",
    )


@router.get("/")
async def list_anomalies(
    item_id: Optional[str] = Query(default=None),
    facility_id: Optional[str] = Query(default=None),
    is_anomaly: Optional[int] = Query(default=None, ge=0, le=1),
    is_acknowledged: Optional[bool] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    filters = AnomalyFilter(
        item_id=item_id,
        facility_id=facility_id,
        is_anomaly=is_anomaly,
        is_acknowledged=is_acknowledged,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    anomalies, total = await anomaly_service.get_anomalies(db, filters)

    return paginated_response(
        data=[anomaly.model_dump(mode="json") for anomaly in anomalies],
        total=total,
        page=page,
        limit=limit,
        message="Anomalies fetched successfully",
    )


@router.get("/{id}")
async def get_anomaly(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    anomaly = await anomaly_service.get_anomaly_by_id(db, id)

    return success_response(
        data=anomaly.model_dump(mode="json"),
        message="Anomaly fetched successfully",
    )


@router.patch("/{id}/acknowledge")
async def acknowledge_anomaly(
    id: str,
    data: AnomalyAcknowledgeRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_WRITE])),
):
    anomaly = await anomaly_service.acknowledge(
        db=db,
        id=id,
        user_id=str(current_user["_id"]),
        notes=data.notes,
    )

    return success_response(
        data=anomaly.model_dump(mode="json"),
        message="Anomaly acknowledged successfully",
    )