from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.exception_handler import ValidationException
from app.core.permissions import REPORT_GENERATE, REPORT_READ
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.report_schema import ReportGenerateRequest
from app.services import report_service

router = APIRouter()


@router.post("/generate")
async def generate_report(
    data: ReportGenerateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([REPORT_GENERATE])),
):
    if data.period_end <= data.period_start:
        raise ValidationException("period_end must be greater than period_start")

    if data.report_type == "daily_summary":
        report = await report_service.generate_daily_summary(
            db=db,
            period_start=data.period_start,
            period_end=data.period_end,
            user_id=str(current_user["_id"]),
        )
    elif data.report_type == "stockout_risk":
        report = await report_service.generate_stockout_risk_report(
            db=db,
            period_start=data.period_start,
            period_end=data.period_end,
            user_id=str(current_user["_id"]),
        )
    elif data.report_type == "vendor_performance":
        report = await report_service.generate_vendor_performance_report(
            db=db,
            period_start=data.period_start,
            period_end=data.period_end,
            user_id=str(current_user["_id"]),
        )
    elif data.report_type == "anomaly_summary":
        report = await report_service.generate_anomaly_summary_report(
            db=db,
            period_start=data.period_start,
            period_end=data.period_end,
            user_id=str(current_user["_id"]),
        )
    else:
        raise ValidationException("Unsupported report type")
    return success_response(
        data=report.model_dump(mode="json"),
        message="Report generation started successfully",
    )


@router.get("/")
async def list_reports(
    report_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([REPORT_READ])),
):
    reports, total = await report_service.get_reports(
        db=db,
        page=page,
        limit=limit,
        report_type=report_type,
    )

    return paginated_response(
        data=[report.model_dump(mode="json") for report in reports],
        total=total,
        page=page,
        limit=limit,
        message="Reports fetched successfully",
    )


@router.get("/{id}")
async def get_report(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([REPORT_READ])),
):
    report = await report_service.get_report(db, id)

    return success_response(
        data=report.model_dump(mode="json"),
        message="Report fetched successfully",
    )


@router.get("/{id}/download")
async def download_report(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([REPORT_READ])),
):
    file_path = await report_service.get_report_file(db, id)

    return FileResponse(
        path=file_path,
        filename=Path(file_path).name,
        media_type="application/octet-stream",
    )