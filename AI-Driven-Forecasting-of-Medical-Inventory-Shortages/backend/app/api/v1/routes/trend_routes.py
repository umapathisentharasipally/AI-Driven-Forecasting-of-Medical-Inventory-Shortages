from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import PREDICTION_READ, PREDICTION_RUN
from app.core.response_handler import paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.trend_schema import TrendComputeRequest
from app.services import trend_service

router = APIRouter()


@router.post("/compute")
async def compute_forecast(
    data: TrendComputeRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_RUN])),
):
    trend = await trend_service.compute_forecast(
        db=db,
        request=data,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=trend.model_dump(mode="json"),
        message="Demand forecast computed successfully",
    )


@router.get("/")
async def list_trends(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    trends, total = await trend_service.list_trends(
        db=db,
        page=page,
        limit=limit,
    )

    return paginated_response(
        data=[trend.model_dump(mode="json") for trend in trends],
        total=total,
        page=page,
        limit=limit,
        message="Trends fetched successfully",
    )


@router.get("/item/{item_id}")
async def get_item_trends(
    item_id: str,
    facility_id: str = Query(...),
    period: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    trends = await trend_service.get_trends(
        db=db,
        item_id=item_id,
        facility_id=facility_id,
        period=period,
    )

    return success_response(
        data=[trend.model_dump(mode="json") for trend in trends],
        message="Item trends fetched successfully",
    )