import csv
import io
from typing import List

from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.validation_utils import to_object_id
from app.repositories import inventory_repository, vendor_repositoryfrom
from backend.app.repositories import vendor_repository 
from app.schemas.upload_schema import UploadResponse
from app.utils.date_utils import parse_date, utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)

INVENTORY_REQUIRED_COLUMNS = {
    "item_id",
    "facility_id",
    "item_name",
    "category",
    "current_stock_on_hand",
    "safety_stock_level",
    "avg_daily_usage_last_30d",
    "vendor_id",
    "vendor_reliability_score",
}

CONSUMPTION_REQUIRED_COLUMNS = {
    "item_id",
    "facility_id",
    "quantity_used",
    "consumed_at",
    "department",
}


def _decode_csv(raw: bytes) -> str:
    return raw.decode("utf-8-sig")


def _to_float(value: str, field: str) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"{field} must be numeric") from exc


async def upload_inventory_csv(
    db: AsyncIOMotorDatabase,
    file: UploadFile,
    current_user_id: str,
) -> UploadResponse:
    raw = await file.read()
    decoded = _decode_csv(raw)
    reader = csv.DictReader(io.StringIO(decoded))

    errors: List[str] = []
    valid_rows: List[dict] = []
    processed = 0

    if not reader.fieldnames:
        return UploadResponse(
            filename=file.filename or "unknown.csv",
            rows_processed=0,
            rows_failed=0,
            errors=["CSV headers missing"],
            created_at=utc_now(),
        )

    missing = INVENTORY_REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        return UploadResponse(
            filename=file.filename or "unknown.csv",
            rows_processed=0,
            rows_failed=0,
            errors=[f"Missing required columns: {sorted(missing)}"],
            created_at=utc_now(),
        )

    for row_number, row in enumerate(reader, start=2):
        processed += 1
        try:
            for col in INVENTORY_REQUIRED_COLUMNS:
                if not row.get(col):
                    raise ValueError(f"{col} is required")

            current_stock = _to_float(row["current_stock_on_hand"], "current_stock_on_hand")
            safety_stock = _to_float(row["safety_stock_level"], "safety_stock_level")
            avg_usage = _to_float(row["avg_daily_usage_last_30d"], "avg_daily_usage_last_30d")

            if current_stock < 0:
                raise ValueError("current_stock_on_hand cannot be negative")
            if safety_stock <= 0:
                raise ValueError("safety_stock_level must be greater than zero")
            vendor_id = row["vendor_id"].strip()
            vendor = await vendor_repository.get_by_id(db, vendor_id)
            if not vendor:
                raise ValueError("vendor_id does not exist")
            valid_rows.append(
                {
                    "item_id": row["item_id"].strip(),
                    "facility_id": row["facility_id"].strip(),
                    "item_name": row["item_name"].strip(),
                    "category": row["category"].strip(),
                    "unit_of_measure": row.get("unit_of_measure", "unit"),
                    "current_stock_on_hand": current_stock,
                    "safety_stock_level": safety_stock,
                    "days_of_supply_on_hand": current_stock / avg_usage if avg_usage > 0 else 0,
                    "avg_daily_usage_last_30d": avg_usage,
                    "avg_daily_usage_last_90d": _to_float(row.get("avg_daily_usage_last_90d", "0"), "avg_daily_usage_last_90d"),
                    "usage_cv_last_90d": _to_float(row.get("usage_cv_last_90d", "0"), "usage_cv_last_90d"),
                    "stock_as_pct_of_safety_level": (current_stock / safety_stock) * 100,
                    "reorder_point": _to_float(row.get("reorder_point", "0"), "reorder_point"),
                    "reorder_quantity": _to_float(row.get("reorder_quantity", "0"), "reorder_quantity"),
                    "vendor_id": to_object_id(vendor_id),
                    "vendor_reliability_score": _to_float(row["vendor_reliability_score"], "vendor_reliability_score"),
                    "actual_avg_lead_time_last_6m": _to_float(row.get("actual_avg_lead_time_last_6m", "0"), "actual_avg_lead_time_last_6m"),
                    "lead_time_variability_days": _to_float(row.get("lead_time_variability_days", "0"), "lead_time_variability_days"),
                    "backorder_frequency_last_12m": _to_float(row.get("backorder_frequency_last_12m", "0"), "backorder_frequency_last_12m"),
                    "expiry_date": parse_date(row["expiry_date"]) if row.get("expiry_date") else None,
                    "department_tags": [row["department"].strip()] if row.get("department") else [],
                    "is_critical": str(row.get("is_critical", "false")).lower() in {"true", "1", "yes"},
                    "is_active": True,
                    "last_restocked_at": None,
                    "snapshot_date": utc_now(),
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                }
            )

        except Exception as exc:
            errors.append(f"Row {row_number}: {exc}")

    if valid_rows:
        await inventory_repository.bulk_upsert(db, valid_rows)

    return UploadResponse(
        filename=file.filename or "inventory.csv",
        rows_processed=processed,
        rows_failed=len(errors),
        errors=errors,
        created_at=utc_now(),
    )


async def upload_consumption_csv(
    db: AsyncIOMotorDatabase,
    file: UploadFile,
    current_user_id: str,
) -> UploadResponse:
    raw = await file.read()
    decoded = _decode_csv(raw)
    reader = csv.DictReader(io.StringIO(decoded))

    errors: List[str] = []
    rows: List[dict] = []
    processed = 0

    if not reader.fieldnames:
        return UploadResponse(
            filename=file.filename or "unknown.csv",
            rows_processed=0,
            rows_failed=0,
            errors=["CSV headers missing"],
            created_at=utc_now(),
        )

    missing = CONSUMPTION_REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        return UploadResponse(
            filename=file.filename or "unknown.csv",
            rows_processed=0,
            rows_failed=0,
            errors=[f"Missing required columns: {sorted(missing)}"],
            created_at=utc_now(),
        )

    for row_number, row in enumerate(reader, start=2):
        processed += 1
        try:
            for col in CONSUMPTION_REQUIRED_COLUMNS:
                if not row.get(col):
                    raise ValueError(f"{col} is required")

            quantity = _to_float(row["quantity_used"], "quantity_used")
            if quantity <= 0:
                raise ValueError("quantity_used must be greater than zero")

            rows.append(
                {
                    "item_id": row["item_id"].strip(),
                    "facility_id": row["facility_id"].strip(),
                    "quantity_used": quantity,
                    "consumed_at": parse_date(row["consumed_at"]),
                    "department": row["department"].strip(),
                    "recorded_by": current_user_id,
                    "created_at": utc_now(),
                }
            )

        except Exception as exc:
            errors.append(f"Row {row_number}: {exc}")

    if rows:
        result = await db["consumption_logs"].insert_many(rows)
        logger.info(f"Inserted consumption training batch: {len(result.inserted_ids)} rows")

    return UploadResponse(
        filename=file.filename or "consumption.csv",
        rows_processed=processed,
        rows_failed=len(errors),
        errors=errors,
        created_at=utc_now(),
    )