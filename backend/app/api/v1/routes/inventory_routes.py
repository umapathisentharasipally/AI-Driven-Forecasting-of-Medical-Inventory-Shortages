from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import INVENTORY_DELETE, INVENTORY_READ, INVENTORY_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.inventory_schema import (
    InventoryFilter,
    InventoryItemCreate,
    InventoryItemUpdate,
    StockAdjustRequest,
)
from app.services import inventory_service

router = APIRouter()


@router.post("/")
async def create_item(
    data: InventoryItemCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_WRITE])),
):
    item = await inventory_service.create_item(db, data)
    return created_response(
        data=item.model_dump(mode="json"),
        message="Inventory item created successfully",
    )


@router.get("/")
async def list_items(
    category: Optional[str] = Query(default=None),
    facility_id: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
    is_critical: Optional[bool] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    below_safety_stock: Optional[bool] = Query(default=None),
    vendor_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_READ])),
):
    filters = InventoryFilter(
        category=category,
        facility_id=facility_id,
        department=department,
        is_critical=is_critical,
        is_active=is_active,
        below_safety_stock=below_safety_stock,
        vendor_id=vendor_id,
        page=page,
        limit=limit,
    )

    items, total = await inventory_service.list_items(db, filters)

    return paginated_response(
        data=[item.model_dump(mode="json") for item in items],
        total=total,
        page=page,
        limit=limit,
        message="Inventory items fetched successfully",
    )


@router.get("/below-safety-stock")
async def get_below_safety_stock(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_READ])),
):
    items = await inventory_service.get_below_safety_stock(db)
    return success_response(
        data=[item.model_dump(mode="json") for item in items],
        message="Below safety stock items fetched successfully",
    )


@router.get("/expiring-soon")
async def get_expiring_soon(
    days: int = Query(default=30, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_READ])),
):
    items = await inventory_service.get_expiring_soon(db, days)
    return success_response(
        data=[item.model_dump(mode="json") for item in items],
        message="Expiring inventory items fetched successfully",
    )

@router.post("/bulk-import")
async def bulk_import(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_WRITE])),
):
    result = await inventory_service.bulk_import_csv(db, file)
    return success_response(
        data=result,
        message="Inventory CSV processed successfully",
    )

@router.get("/{id}")
async def get_item(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_READ])),
):
    item = await inventory_service.get_item(db, id)
    return success_response(
        data=item.model_dump(mode="json"),
        message="Inventory item fetched successfully",
    )


@router.patch("/{id}")
async def update_item(
    id: str,
    data: InventoryItemUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_WRITE])),
):
    item = await inventory_service.update_item(db, id, data)
    return success_response(
        data=item.model_dump(mode="json"),
        message="Inventory item updated successfully",
    )


@router.delete("/{id}")
async def delete_item(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_DELETE])),
):
    await inventory_service.delete_item(db, id)
    return success_response(message="Inventory item deleted successfully")


@router.patch("/{id}/stock")
async def adjust_stock(
    id: str,
    data: StockAdjustRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([INVENTORY_WRITE])),
):
    item = await inventory_service.adjust_stock(
        db=db,
        id=id,
        data=data,
        current_user_id=str(current_user["_id"]),
    )

    return success_response(
        data=item.model_dump(mode="json"),
        message="Stock adjusted successfully",
    )


