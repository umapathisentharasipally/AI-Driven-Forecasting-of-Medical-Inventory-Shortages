from fastapi import APIRouter, Depends, File, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import INVENTORY_WRITE
from app.core.response_handler import success_response
from app.core.role_checker import RoleChecker
from app.services import upload_service

router = APIRouter()


@router.post("/inventory")
async def upload_inventory_csv(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_WRITE])),
):
    result = await upload_service.upload_inventory_csv(
        db=db,
        file=file,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=result.model_dump(mode="json"),
        message="Inventory CSV uploaded successfully",
    )


@router.post("/consumption")
async def upload_consumption_csv(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_WRITE])),
):
    result = await upload_service.upload_consumption_csv(
        db=db,
        file=file,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=result.model_dump(mode="json"),
        message="Consumption CSV uploaded successfully",
    )