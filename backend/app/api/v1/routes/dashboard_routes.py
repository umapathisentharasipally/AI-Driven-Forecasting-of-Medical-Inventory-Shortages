from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.permissions import ALERT_READ, PREDICTION_READ
from app.core.response_handler import success_response
from app.core.role_checker import RoleChecker
from app.services import alert_service, dashboard_service

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    summary = await dashboard_service.get_summary(db)

    return success_response(
        data=summary,
        message="Dashboard summary fetched successfully",
    )


@router.get("/top-risk")
async def top_risk_items(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([PREDICTION_READ])),
):
    pipeline = [
        {"$sort": {"stockout_probability": -1, "prediction_date": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": {"$toString": "$_id"},
                "item_id": 1,
                "facility_id": 1,
                "risk_level": 1,
                "stockout_probability": 1,
                "days_of_supply_on_hand": 1,
                "prediction_date": 1,
            }
        },
    ]

    items = await db["predictions"].aggregate(pipeline).to_list(length=limit)

    return success_response(
        data=items,
        message="Top risk predictions fetched successfully",
    )


@router.get("/alert-counts")
async def alert_counts(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([ALERT_READ])),
):
    counts = await alert_service.get_dashboard_counts(db)

    return success_response(
        data=counts.model_dump(mode="json"),
        message="Alert counts fetched successfully",
    )