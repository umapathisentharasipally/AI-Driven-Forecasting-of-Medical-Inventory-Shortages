from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.security import get_current_active_user
from app.core.response_handler import success_response

router = APIRouter()

DEFAULT_SETTINGS = {
    "app_name": "MedInv Forecast",
    "low_stock_threshold": 10,
    "expiry_alert_days": 30,
    "currency": "INR",
    "email_alerts_enabled": True,
}


@router.get("/")
async def get_settings(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    settings = await db["settings"].find_one({"key": "application"}, {"_id": 0})

    if not settings:
        settings = {"key": "application", **DEFAULT_SETTINGS}

    settings.pop("key", None)

    return success_response(
        data=settings,
        message="Settings fetched successfully"
    )


@router.put("/")
async def update_settings(
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user),
):
    allowed_keys = set(DEFAULT_SETTINGS.keys())
    update_data = {
        key: value
        for key, value in payload.items()
        if key in allowed_keys
    }

    await db["settings"].update_one(
        {"key": "application"},
        {
            "$set": update_data,
            "$setOnInsert": {"key": "application"},
        },
        upsert=True,
    )

    settings = await db["settings"].find_one({"key": "application"}, {"_id": 0})
    settings.pop("key", None)

    return success_response(
        data=settings,
        message="Settings updated successfully"
    )