import os
import tempfile
from typing import List, Tuple
from uuid import uuid4

import asyncio
from app.services import alert_service

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.settings import settings
from app.core.exception_handler import MLInferenceException, NotFoundException
from app.repositories import anomaly_repository, inventory_repository
from app.schemas.anomaly_schema import (
    AnomalyAcknowledgeRequest,
    AnomalyFilter,
    AnomalyResponse,
)
from app.utils.date_utils import utc_now
from app.utils.validation_utils import validate_pagination

ANOMALY_FEATURE_COLUMNS = [
    "avg_daily_usage_last_30d",
    "avg_daily_usage_last_90d",
    "usage_cv_last_90d",
    "current_stock_on_hand",
    "safety_stock_level",
    "days_of_supply_on_hand",
    "stock_as_pct_of_safety_level",
    "vendor_reliability_score",
    "actual_avg_lead_time_last_6m",
    "lead_time_variability_days",
    "backorder_frequency_last_12m",
]


def to_anomaly_response(anomaly: dict) -> AnomalyResponse:
    return AnomalyResponse(
        id=str(anomaly["_id"]),
        item_id=anomaly["item_id"],
        facility_id=anomaly["facility_id"],
        inventory_doc_id=anomaly["inventory_doc_id"],
        detected_at=anomaly["detected_at"],
        anomaly_score=float(anomaly["anomaly_score"]),
        is_anomaly=int(anomaly["is_anomaly"]),
        input_snapshot=anomaly["input_snapshot"],
        is_acknowledged=bool(anomaly["is_acknowledged"]),
        acknowledged_by=anomaly.get("acknowledged_by"),
        acknowledged_at=anomaly.get("acknowledged_at"),
        notes=anomaly.get("notes"),
        created_at=anomaly["created_at"],
    )


def _inventory_to_anomaly_row(item: dict) -> dict:
    row = {
        "inventory_doc_id": str(item["_id"]),
        "item_id": item["item_id"],
        "facility_id": item["facility_id"],
        "item_name": item.get("item_name", item["item_id"]),
    }

    for field in ANOMALY_FEATURE_COLUMNS:
        row[field] = item[field]

    return row


async def detect_for_all(
    db: AsyncIOMotorDatabase,
    facility_id: str | None,
    current_user_id: str,
) -> dict:
    query = {"is_active": True}
    if facility_id:
        query["facility_id"] = facility_id

    items = await db["inventory_items"].find(query).to_list(length=None)

    if not items:
        return {
            "total_scanned": 0,
            "anomalies_detected": 0,
            "saved": 0,
        }

    rows = [_inventory_to_anomaly_row(item) for item in items]
    df = pd.DataFrame(rows)

    temp_path = os.path.join(
        tempfile.gettempdir(),
        f"anomaly_input_{uuid4()}.csv",
    )

    try:
        df.to_csv(temp_path, index=False)

        from ml.src.inference.detect_anomalies import detect_anomalies

        try:
            output_df = detect_anomalies(
                input_path=temp_path,
                config_path=f"{settings.ML_CONFIGS_PATH}/anomaly_config.yaml",
            )
        except Exception as exc:
            raise MLInferenceException("Anomaly detection failed") from exc

        anomaly_docs = []
        detected_at = utc_now()

        for index, output_row in output_df.iterrows():
            is_anomaly = int(output_row.get("is_anomaly", 0))

            if is_anomaly != 1:
                continue

            source_row = rows[index]

            input_snapshot = {
                field: source_row[field] for field in ANOMALY_FEATURE_COLUMNS
            }
            input_snapshot["item_name"] = source_row.get("item_name", source_row["item_id"])

            anomaly_docs.append(
                {
                    "item_id": source_row["item_id"],
                    "facility_id": source_row["facility_id"],
                    "inventory_doc_id": source_row["inventory_doc_id"],
                    "detected_at": detected_at,
                    "anomaly_score": float(output_row["anomaly_score"]),
                    "is_anomaly": is_anomaly,
                    "input_snapshot": input_snapshot,
                    "is_acknowledged": False,
                    "acknowledged_by": None,
                    "acknowledged_at": None,
                    "notes": None,
                    "created_at": detected_at,
                }
            )

        saved = 0

        for anomaly_doc in anomaly_docs:
            created = await anomaly_repository.create(db, anomaly_doc)
            saved += 1

            asyncio.create_task(
                alert_service.create_anomaly_alert(
                    db=db,
                    item_id=created["item_id"],
                    facility_id=created["facility_id"],
                    inventory_doc_id=created["inventory_doc_id"],
                    anomaly_id=str(created["_id"]),
                    anomaly_score=float(created["anomaly_score"]),
                    item_name=created["input_snapshot"].get(
                        "item_name",
                        created["item_id"],
                    ),
                )
            )

        return {
            "total_scanned": len(items),
            "anomalies_detected": len(anomaly_docs),
            "saved": saved,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


async def get_anomalies(
    db: AsyncIOMotorDatabase,
    filters: AnomalyFilter,
) -> Tuple[List[AnomalyResponse], int]:
    page, limit = validate_pagination(filters.page, filters.limit)

    anomalies, total = await anomaly_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters=filters.model_dump(exclude_none=True),
    )

    return [to_anomaly_response(anomaly) for anomaly in anomalies], total


async def get_anomaly_by_id(
    db: AsyncIOMotorDatabase,
    id: str,
) -> AnomalyResponse:
    anomaly = await anomaly_repository.get_by_id(db, id)
    if not anomaly:
        raise NotFoundException("Anomaly not found")

    return to_anomaly_response(anomaly)


async def acknowledge(
    db: AsyncIOMotorDatabase,
    id: str,
    user_id: str,
    notes: str | None,
) -> AnomalyResponse:
    existing = await anomaly_repository.get_by_id(db, id)
    if not existing:
        raise NotFoundException("Anomaly not found")

    updated = await anomaly_repository.acknowledge(
        db=db,
        id=id,
        user_id=user_id,
        notes=notes,
    )

    if not updated:
        raise NotFoundException("Anomaly not found")

    return to_anomaly_response(updated)