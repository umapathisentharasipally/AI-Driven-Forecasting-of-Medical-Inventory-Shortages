import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import ValidationException
from app.schemas.export_schema import ExportResponse
from app.utils.date_utils import utc_now

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

COLLECTION_MAP = {
    "inventory": "inventory_items",
    "predictions": "predictions",
    "alerts": "alerts",
    "anomalies": "anomalies",
    "audit_logs": "audit_logs",
}


def _serialize(value: Any):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _serialize_doc(doc: dict) -> dict:
    return {key: _serialize(value) for key, value in doc.items()}


async def export_collection(
    db: AsyncIOMotorDatabase,
    export_type: str,
    filters: dict,
    format: str,
    current_user_id: str,
) -> ExportResponse:
    if export_type not in COLLECTION_MAP:
        raise ValidationException("Invalid export type")

    if format not in {"csv", "json"}:
        raise ValidationException("Invalid export format")

    collection_name = COLLECTION_MAP[export_type]
    filename = f"{export_type}_{utc_now().strftime('%Y%m%d_%H%M%S')}.{format}"
    filepath = EXPORT_DIR / filename

    data: List[dict] = []
    skip = 0
    batch_size = 1000

    while True:
        batch = await (
            db[collection_name]
            .find(_sanitize_filters(filters))
            .skip(skip)
            .limit(batch_size)
            .to_list(length=batch_size)
        )

        if not batch:
            break

        data.extend(_serialize_doc(doc) for doc in batch)

        if len(batch) < batch_size:
            break

        skip += batch_size

    if format == "csv":
        _write_csv(data, filepath)
    else:
        _write_json(data, filepath)

    return ExportResponse(
        filename=filename,
        row_count=len(data),
        download_url=f"/api/v1/export/download/{filename}",
        created_at=utc_now(),
    )


def _flatten_for_csv(row: dict) -> dict:
    flattened = {}

    for key, value in row.items():
        if isinstance(value, (dict, list)):
            flattened[key] = json.dumps(value, default=str)
        else:
            flattened[key] = value

    return flattened


def _write_csv(data: List[dict], filepath: Path) -> None:
    if not data:
        filepath.write_text("", encoding="utf-8")
        return

    flattened_data = [_flatten_for_csv(row) for row in data]
    fieldnames = sorted({key for row in flattened_data for key in row.keys()})

    with filepath.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in flattened_data:
            writer.writerow(row)


def _write_json(data: List[dict], filepath: Path) -> None:
    with filepath.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def _sanitize_filters(filters: dict) -> dict:
    safe = {}

    for key, value in filters.items():
        if key.startswith("$"):
            continue

        if isinstance(value, dict):
            nested = {
                nested_key: nested_value
                for nested_key, nested_value in value.items()
                if not nested_key.startswith("$")
            }
            safe[key] = nested
        else:
            safe[key] = value

    return safe