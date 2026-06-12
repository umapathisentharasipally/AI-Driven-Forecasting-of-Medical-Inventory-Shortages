from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import ConflictException, NotFoundException
from app.repositories import inventory_repository, vendor_repository
from app.schemas.inventory_schema import InventoryItemResponse
from app.schemas.vendor_schema import VendorCreate, VendorResponse, VendorUpdate
from app.services.inventory_service import to_inventory_response
from app.utils.date_utils import utc_now
from app.utils.validation_utils import validate_pagination


def to_vendor_response(vendor: dict) -> VendorResponse:
    return VendorResponse(
        id=str(vendor["_id"]),
        vendor_code=vendor["vendor_code"],
        name=vendor["name"],
        contact_email=vendor["contact_email"],
        contact_phone=vendor.get("contact_phone"),
        address=vendor.get("address"),
        avg_lead_time_days=float(vendor["avg_lead_time_days"]),
        reliability_score=float(vendor["reliability_score"]),
        contract_expiry=vendor.get("contract_expiry"),
        is_active=bool(vendor["is_active"]),
        created_at=vendor["created_at"],
    )


async def create_vendor(
    db: AsyncIOMotorDatabase,
    data: VendorCreate,
) -> VendorResponse:
    existing = await vendor_repository.get_by_vendor_code(db, data.vendor_code)
    if existing:
        raise ConflictException("Vendor code already exists")

    vendor_doc = data.model_dump()
    if vendor_doc.get("address") is not None:
        vendor_doc["address"] = data.address.model_dump()

    vendor_doc["is_active"] = True
    vendor_doc["created_at"] = utc_now()

    created = await vendor_repository.create(db, vendor_doc)
    return to_vendor_response(created)


async def get_vendor(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
) -> VendorResponse:
    vendor = await vendor_repository.get_by_id(db, vendor_id)
    if not vendor:
        raise NotFoundException("Vendor not found")
    return to_vendor_response(vendor)


async def list_vendors(
    db: AsyncIOMotorDatabase,
    page: int,
    limit: int,
    is_active: Optional[bool],
) -> Tuple[List[VendorResponse], int]:
    page, limit = validate_pagination(page, limit)

    vendors, total = await vendor_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        is_active=is_active,
    )

    return [to_vendor_response(vendor) for vendor in vendors], total


async def update_vendor(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    data: VendorUpdate,
) -> VendorResponse:
    existing = await vendor_repository.get_by_id(db, vendor_id)
    if not existing:
        raise NotFoundException("Vendor not found")

    update_data = data.model_dump(exclude_unset=True)

    if "address" in update_data and data.address is not None:
        update_data["address"] = data.address.model_dump()

    updated = await vendor_repository.update(db, vendor_id, update_data)
    if not updated:
        raise NotFoundException("Vendor not found")

    return to_vendor_response(updated)


async def deactivate_vendor(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
) -> None:
    existing = await vendor_repository.get_by_id(db, vendor_id)
    if not existing:
        raise NotFoundException("Vendor not found")

    deleted = await vendor_repository.soft_delete(db, vendor_id)
    if not deleted:
        raise NotFoundException("Vendor not found")


async def get_vendor_items(
    db: AsyncIOMotorDatabase,
    vendor_id: str,
    page: int,
    limit: int,
) -> Tuple[List[InventoryItemResponse], int]:
    vendor = await vendor_repository.get_by_id(db, vendor_id)
    if not vendor:
        raise NotFoundException("Vendor not found")

    page, limit = validate_pagination(page, limit)

    items, total = await inventory_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters={
            "vendor_id": vendor_id,
            "is_active": True,
        },
    )

    return [to_inventory_response(item) for item in items], total