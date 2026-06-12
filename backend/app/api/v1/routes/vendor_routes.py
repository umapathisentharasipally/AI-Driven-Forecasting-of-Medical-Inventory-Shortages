from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.core.permissions import VENDOR_READ, VENDOR_WRITE
from app.core.response_handler import created_response, paginated_response, success_response
from app.core.role_checker import RoleChecker
from app.schemas.vendor_schema import VendorCreate, VendorUpdate
from app.services import vendor_service

router = APIRouter()


@router.post("/")
async def create_vendor(
    data: VendorCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([VENDOR_WRITE])),
):
    vendor = await vendor_service.create_vendor(db, data)
    return created_response(
        data=vendor.model_dump(mode="json"),
        message="Vendor created successfully",
    )


@router.get("/")
async def list_vendors(
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([VENDOR_READ])),
):
    vendors, total = await vendor_service.list_vendors(
        db=db,
        page=page,
        limit=limit,
        is_active=is_active,
    )

    return paginated_response(
        data=[vendor.model_dump(mode="json") for vendor in vendors],
        total=total,
        page=page,
        limit=limit,
        message="Vendors fetched successfully",
    )


@router.get("/{id}")
async def get_vendor(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([VENDOR_READ])),
):
    vendor = await vendor_service.get_vendor(db, id)
    return success_response(
        data=vendor.model_dump(mode="json"),
        message="Vendor fetched successfully",
    )


@router.patch("/{id}")
async def update_vendor(
    id: str,
    data: VendorUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([VENDOR_WRITE])),
):
    vendor = await vendor_service.update_vendor(db, id, data)
    return success_response(
        data=vendor.model_dump(mode="json"),
        message="Vendor updated successfully",
    )


@router.delete("/{id}")
async def deactivate_vendor(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([VENDOR_WRITE])),
):
    await vendor_service.deactivate_vendor(db, id)
    return success_response(message="Vendor deactivated successfully")


@router.get("/{id}/items")
async def get_vendor_items(
    id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(RoleChecker([VENDOR_READ])),
):
    items, total = await vendor_service.get_vendor_items(
        db=db,
        vendor_id=id,
        page=page,
        limit=limit,
    )

    return paginated_response(
        data=[item.model_dump(mode="json") for item in items],
        total=total,
        page=page,
        limit=limit,
        message="Vendor inventory items fetched successfully",
    )