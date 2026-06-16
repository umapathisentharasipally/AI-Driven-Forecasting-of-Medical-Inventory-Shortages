import csv
import io
from typing import List, Tuple
# ADD imports at top
import asyncio
from app.services import alert_service

from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import ConflictException, NotFoundException, ValidationException
from app.repositories import inventory_repository, vendor_repository
from app.schemas.inventory_schema import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    StockAdjustRequest,
)
from app.utils.date_utils import parse_date, utc_now
from app.utils.logger import get_logger
from app.utils.validation_utils import to_object_id, validate_pagination

logger = get_logger(__name__)


REQUIRED_CSV_FIELDS = {
    "item_id",
    "facility_id",
    "item_name",
    "category",
    "unit_of_measure",
    "current_stock_on_hand",
    "safety_stock_level",
    "avg_daily_usage_last_30d",
    "avg_daily_usage_last_90d",
    "usage_cv_last_90d",
    "reorder_point",
    "reorder_quantity",
    "vendor_id",
    "vendor_reliability_score",
    "actual_avg_lead_time_last_6m",
    "lead_time_variability_days",
    "backorder_frequency_last_12m",
}


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _calculate_days_of_supply(current_stock: float, avg_daily_usage: float) -> float:
    return _safe_divide(current_stock, avg_daily_usage)


def _calculate_stock_as_pct_of_safety(current_stock: float, safety_stock: float) -> float:
    return _safe_divide(current_stock, safety_stock) * 100


def to_inventory_response(item: dict) -> InventoryItemResponse:
    return InventoryItemResponse(
        id=str(item["_id"]),
        item_id=item["item_id"],
        facility_id=item["facility_id"],
        item_name=item["item_name"],
        category=item["category"],
        unit_of_measure=item["unit_of_measure"],
        current_stock_on_hand=float(item["current_stock_on_hand"]),
        safety_stock_level=float(item["safety_stock_level"]),
        days_of_supply_on_hand=float(item["days_of_supply_on_hand"]),
        avg_daily_usage_last_30d=float(item["avg_daily_usage_last_30d"]),
        avg_daily_usage_last_90d=float(item["avg_daily_usage_last_90d"]),
        usage_cv_last_90d=float(item["usage_cv_last_90d"]),
        stock_as_pct_of_safety_level=float(item["stock_as_pct_of_safety_level"]),
        reorder_point=float(item["reorder_point"]),
        reorder_quantity=float(item["reorder_quantity"]),
        vendor_id=str(item["vendor_id"]),
        vendor_reliability_score=float(item["vendor_reliability_score"]),
        actual_avg_lead_time_last_6m=float(item["actual_avg_lead_time_last_6m"]),
        lead_time_variability_days=float(item["lead_time_variability_days"]),
        backorder_frequency_last_12m=float(item["backorder_frequency_last_12m"]),
        expiry_date=item.get("expiry_date"),
        department_tags=item.get("department_tags", []),
        is_critical=bool(item["is_critical"]),
        is_active=bool(item["is_active"]),
        last_restocked_at=item.get("last_restocked_at"),
        snapshot_date=item["snapshot_date"],
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


async def create_item(
    db: AsyncIOMotorDatabase,
    data: InventoryItemCreate,
) -> InventoryItemResponse:
    existing = await inventory_repository.get_by_item_facility(
        db=db,
        item_id=data.item_id,
        facility_id=data.facility_id,
    )
    if existing:
        raise ConflictException("Inventory item already exists for this facility")

    vendor = await vendor_repository.get_by_id(db, data.vendor_id)
    if not vendor:
        raise NotFoundException("Vendor not found")

    now = utc_now()
    current_stock = float(data.current_stock_on_hand)
    avg_usage_30d = float(data.avg_daily_usage_last_30d)
    safety_stock = float(data.safety_stock_level)

    item_doc = data.model_dump()
    item_doc["vendor_id"] = to_object_id(data.vendor_id)
    item_doc["days_of_supply_on_hand"] = _calculate_days_of_supply(
        current_stock,
        avg_usage_30d,
    )
    item_doc["stock_as_pct_of_safety_level"] = _calculate_stock_as_pct_of_safety(
        current_stock,
        safety_stock,
    )
    item_doc["snapshot_date"] = now
    item_doc["created_at"] = now
    item_doc["updated_at"] = now

    created = await inventory_repository.create(db, item_doc)
    return to_inventory_response(created)


async def get_item(
    db: AsyncIOMotorDatabase,
    id: str,
) -> InventoryItemResponse:
    item = await inventory_repository.get_by_id(db, id)
    if not item:
        raise NotFoundException("Inventory item not found")
    return to_inventory_response(item)


async def list_items(
    db: AsyncIOMotorDatabase,
    filters,
) -> Tuple[List[InventoryItemResponse], int]:
    page, limit = validate_pagination(filters.page, filters.limit)

    items, total = await inventory_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters=filters.model_dump(exclude_none=True),
    )

    return [to_inventory_response(item) for item in items], total


async def update_item(
    db: AsyncIOMotorDatabase,
    id: str,
    data: InventoryItemUpdate,
) -> InventoryItemResponse:
    existing = await inventory_repository.get_by_id(db, id)
    if not existing:
        raise NotFoundException("Inventory item not found")

    update_data = data.model_dump(exclude_unset=True)

    if "vendor_id" in update_data and update_data["vendor_id"]:
        vendor = await vendor_repository.get_by_id(db, update_data["vendor_id"])
        if not vendor:
            raise NotFoundException("Vendor not found")
        update_data["vendor_id"] = to_object_id(update_data["vendor_id"])

    current_stock = float(
        update_data.get("current_stock_on_hand", existing["current_stock_on_hand"])
    )
    avg_usage_30d = float(
        update_data.get("avg_daily_usage_last_30d", existing["avg_daily_usage_last_30d"])
    )
    safety_stock = float(
        update_data.get("safety_stock_level", existing["safety_stock_level"])
    )

    update_data["days_of_supply_on_hand"] = _calculate_days_of_supply(
        current_stock,
        avg_usage_30d,
    )
    update_data["stock_as_pct_of_safety_level"] = _calculate_stock_as_pct_of_safety(
        current_stock,
        safety_stock,
    )
    update_data["snapshot_date"] = utc_now()

    updated = await inventory_repository.update(db, id, update_data)
    if not updated:
        raise NotFoundException("Inventory item not found")

    return to_inventory_response(updated)


async def delete_item(
    db: AsyncIOMotorDatabase,
    id: str,
) -> None:
    existing = await inventory_repository.get_by_id(db, id)
    if not existing:
        raise NotFoundException("Inventory item not found")

    deleted = await inventory_repository.delete(db, id)
    if not deleted:
        raise NotFoundException("Inventory item not found")


async def adjust_stock(
    db: AsyncIOMotorDatabase,
    id: str,
    data: StockAdjustRequest,
    current_user_id: str,
) -> InventoryItemResponse:
    existing = await inventory_repository.get_by_id(db, id)
    if not existing:
        raise NotFoundException("Inventory item not found")

    current_stock = float(existing["current_stock_on_hand"])
    new_stock = current_stock + float(data.delta)

    if new_stock < 0:
        raise ValidationException("Stock adjustment cannot make stock negative")

    updated = await inventory_repository.adjust_stock_atomic(
        db=db,
        id=id,
        delta=float(data.delta),
    )

    if not updated:
        raise NotFoundException("Inventory item not found")

    if data.adjustment_type == "usage":
        now = utc_now()
        await db["consumption_logs"].insert_one(
            {
                "item_id": updated["item_id"],
                "facility_id": updated["facility_id"],
                "quantity_used": abs(float(data.delta)),
                "consumed_at": now,
                "recorded_by": current_user_id,
                "reason": data.reason,
                "created_at": now,
            }
        )

    # NEW
    if float(updated["current_stock_on_hand"]) < float(updated["safety_stock_level"]):
        asyncio.create_task(
            alert_service.create_below_safety_alert(
                db=db,
                item_id=updated["item_id"],
                facility_id=updated["facility_id"],
                inventory_doc_id=str(updated["_id"]),
                current_stock=float(updated["current_stock_on_hand"]),
                safety_level=float(updated["safety_stock_level"]),
                item_name=updated["item_name"],
            )
        )
    return to_inventory_response(updated)


async def get_below_safety_stock(
    db: AsyncIOMotorDatabase,
) -> List[InventoryItemResponse]:
    items = await inventory_repository.get_below_safety_stock(db)
    return [to_inventory_response(item) for item in items]


async def get_expiring_soon(
    db: AsyncIOMotorDatabase,
    days: int,
) -> List[InventoryItemResponse]:
    if days < 1:
        raise ValidationException("days must be greater than or equal to 1")

    items = await inventory_repository.get_expiring_soon(db, days)
    return [to_inventory_response(item) for item in items]


def _parse_optional_datetime(value: str | None):
    if not value:
        return None
    return parse_date(value)


def _parse_bool(value: str | bool | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value

    if value is None or value == "":
        return default

    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _parse_department_tags(value: str | None) -> List[str]:
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _build_csv_item(row: dict) -> dict:
    current_stock = float(row["current_stock_on_hand"])
    safety_stock = float(row["safety_stock_level"])
    avg_usage_30d = float(row["avg_daily_usage_last_30d"])
    now = utc_now()

    return {
        "item_id": row["item_id"].strip(),
        "facility_id": row["facility_id"].strip(),
        "item_name": row["item_name"].strip(),
        "category": row["category"].strip(),
        "unit_of_measure": row["unit_of_measure"].strip(),
        "current_stock_on_hand": current_stock,
        "safety_stock_level": safety_stock,
        "days_of_supply_on_hand": _calculate_days_of_supply(
            current_stock,
            avg_usage_30d,
        ),
        "avg_daily_usage_last_30d": avg_usage_30d,
        "avg_daily_usage_last_90d": float(row["avg_daily_usage_last_90d"]),
        "usage_cv_last_90d": float(row["usage_cv_last_90d"]),
        "stock_as_pct_of_safety_level": _calculate_stock_as_pct_of_safety(
            current_stock,
            safety_stock,
        ),
        "reorder_point": float(row["reorder_point"]),
        "reorder_quantity": float(row["reorder_quantity"]),
        "vendor_id": to_object_id(row["vendor_id"].strip()),        "vendor_reliability_score": float(row["vendor_reliability_score"]),
        "actual_avg_lead_time_last_6m": float(row["actual_avg_lead_time_last_6m"]),
        "lead_time_variability_days": float(row["lead_time_variability_days"]),
        "backorder_frequency_last_12m": float(row["backorder_frequency_last_12m"]),
        "expiry_date": _parse_optional_datetime(row.get("expiry_date")),
        "department_tags": _parse_department_tags(row.get("department_tags")),
        "is_critical": _parse_bool(row.get("is_critical"), default=False),
        "is_active": _parse_bool(row.get("is_active"), default=True),
        "last_restocked_at": _parse_optional_datetime(row.get("last_restocked_at")),
        "snapshot_date": now,
        "created_at": now,
        "updated_at": now,
    }


async def bulk_import_csv(
    db: AsyncIOMotorDatabase,
    file: UploadFile,
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationException("Only CSV files are allowed")

    raw_content = await file.read()

    try:
        decoded = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationException("CSV file must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValidationException("CSV file is empty or headers are missing")

    missing_headers = REQUIRED_CSV_FIELDS - set(reader.fieldnames)
    if missing_headers:
        raise ValidationException(
            "CSV file is missing required headers",
            details={"missing_headers": sorted(missing_headers)},
        )

    items = []
    errors = []
    processed = 0
    failed = 0

    for row_number, row in enumerate(reader, start=2):
        processed += 1

        try:
            for field in REQUIRED_CSV_FIELDS:
                if row.get(field) is None or str(row.get(field)).strip() == "":
                    raise ValidationException(f"Missing required field: {field}")

            vendor = await vendor_repository.get_by_id(db, row["vendor_id"])
            if not vendor:
                raise NotFoundException("Vendor not found")

            items.append(_build_csv_item(row))

        except Exception as exc:
            failed += 1
            errors.append(
                {
                    "row": row_number,
                    "error": str(exc)[:300],
                }
            )
    upsert_result = await inventory_repository.bulk_upsert(db, items)

    return {
        "processed": processed,
        "inserted": upsert_result["inserted"],
        "updated": upsert_result["updated"],
        "failed": failed + upsert_result["failed"],
        "errors": errors,
    }