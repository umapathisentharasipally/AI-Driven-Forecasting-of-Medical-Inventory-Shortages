from typing import List, Tuple
# ADD imports at top
import asyncio
from app.services import alert_service
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exception_handler import MLInferenceException, NotFoundException, ValidationException
from app.repositories import inventory_repository, prediction_repository
from app.schemas.prediction_schema import (
    BatchPredictRequest,
    BatchPredictResponse,
    PredictionFilter,
    RealtimePredictRequest,
    RealtimePredictResponse,
)
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger
from app.utils.validation_utils import validate_pagination

logger = get_logger(__name__)

ML_REQUIRED_FIELDS = [
    "item_id",
    "facility_id",
    "snapshot_date",
    "current_stock_on_hand",
    "safety_stock_level",
    "days_of_supply_on_hand",
    "avg_daily_usage_last_30d",
    "avg_daily_usage_last_90d",
    "usage_cv_last_90d",
    "stock_as_pct_of_safety_level",
    "vendor_reliability_score",
    "actual_avg_lead_time_last_6m",
    "lead_time_variability_days",
    "backorder_frequency_last_12m",
]


def _build_prediction_input(item: dict) -> dict:
    record = {}

    for field in ML_REQUIRED_FIELDS:
        if field not in item:
            raise ValidationException(
                "Inventory item is missing required ML field",
                details={"missing_field": field},
            )
        record[field] = item[field]

    return record


#def _get_model_version(predictor) -> str:
    #return getattr(predictor, "model_version", "unknown")


def to_prediction_response(prediction: dict) -> RealtimePredictResponse:
    return RealtimePredictResponse(
        id=str(prediction["_id"]),
        item_id=prediction["item_id"],
        facility_id=prediction["facility_id"],
        stockout_probability=float(prediction["stockout_probability"]),
        stockout_prediction=int(prediction["stockout_prediction"]),
        risk_level=prediction["risk_level"],
        days_of_supply_on_hand=float(prediction["days_of_supply_on_hand"]),
        model_name=prediction["model_name"],
        model_version=prediction["model_version"],
        prediction_date=prediction["prediction_date"],
        created_at=prediction["created_at"],
    )


def _build_prediction_document(
    item: dict,
    prediction_result: dict,
    feature_snapshot: dict,
    model_version: str,
) -> dict:
    now = utc_now()

    return {
        "item_id": item["item_id"],
        "facility_id": item["facility_id"],
        "inventory_doc_id": str(item["_id"]),
        "model_name": "xgboost",
        "model_version": model_version,
        "prediction_date": now,
        "stockout_probability": float(prediction_result["stockout_probability"]),
        "stockout_prediction": int(prediction_result["stockout_prediction"]),
        "risk_level": prediction_result["risk_level"],
        "days_of_supply_on_hand": float(feature_snapshot["days_of_supply_on_hand"]),
        "feature_snapshot": feature_snapshot,
        "created_at": now,
    }


async def predict_realtime(
    db: AsyncIOMotorDatabase,
    request: RealtimePredictRequest,
    predictor,
    model_version: str,
    current_user_id: str,
) -> RealtimePredictResponse:
    if predictor is None:
        raise MLInferenceException("Realtime predictor is not initialized")

    item = await inventory_repository.get_by_id(db, request.inventory_doc_id)
    if not item or not item.get("is_active", False):
        raise NotFoundException("Active inventory item not found")

    feature_snapshot = _build_prediction_input(item)

    try:
        prediction_result = predictor.predict_one(feature_snapshot)
    except Exception as exc:
        raise MLInferenceException("Realtime prediction failed") from exc

    model_version = model_version or "unknown"
    prediction_doc = _build_prediction_document(
        item=item,
        prediction_result=prediction_result,
        feature_snapshot=feature_snapshot,
        model_version=model_version,
    )

    created = await prediction_repository.create(db, prediction_doc)

    # NEW
    if created["risk_level"] in ["High", "Critical"]:
        asyncio.create_task(
            alert_service.create_stockout_alert(
                db=db,
                item_id=created["item_id"],
                facility_id=created["facility_id"],
                inventory_doc_id=created["inventory_doc_id"],
                prediction_id=str(created["_id"]),
                stockout_probability=float(created["stockout_probability"]),
                risk_level=created["risk_level"],
                item_name=item["item_name"],
            )
        )
    return to_prediction_response(created)


async def predict_batch(
    db: AsyncIOMotorDatabase,
    request: BatchPredictRequest,
    predictor,
    model_version: str,
    current_user_id: str,
) -> BatchPredictResponse:
    if predictor is None:
        raise MLInferenceException("Realtime predictor is not initialized")

    filters = {"is_active": True}

    if request.facility_id:
        filters["facility_id"] = request.facility_id

    if request.run_all:
        items, _ = await inventory_repository.get_all(
            db=db,
            page=1,
            limit=100000,
            filters=filters,
        )
    elif request.item_ids:
        query = {
            "is_active": True,
            "item_id": {"$in": request.item_ids},
        }

        if request.facility_id:
            query["facility_id"] = request.facility_id

        cursor = db["inventory_items"].find(query)
        items = await cursor.to_list(length=None)
    else:
        raise ValidationException(
            "Either run_all must be true or item_ids must be provided"
        )

    succeeded = 0
    failed = 0
    high_risk_count = 0
    critical_count = 0

    for item in items:
        already_done = await prediction_repository.already_predicted_today(
            db=db,
            inventory_doc_id=str(item["_id"]),
        )
        if already_done:
            continue

        try:
            feature_snapshot = _build_prediction_input(item)

            try:
                prediction_result = predictor.predict_one(feature_snapshot)
            except Exception as exc:
                raise MLInferenceException("Batch prediction failed") from exc

            prediction_doc = _build_prediction_document(
                item=item,
                prediction_result=prediction_result,
                feature_snapshot=feature_snapshot,
                model_version=model_version or "unknown",
            )

            created = await prediction_repository.create(db, prediction_doc)
            succeeded += 1

            probability = float(created["stockout_probability"])
            risk_level = created["risk_level"]

            if probability >= 0.7:
                high_risk_count += 1

            if risk_level == "Critical":
                critical_count += 1

            if risk_level in ["High", "Critical"]:
                asyncio.create_task(
                    alert_service.create_stockout_alert(
                        db=db,
                        item_id=created["item_id"],
                        facility_id=created["facility_id"],
                        inventory_doc_id=created["inventory_doc_id"],
                        prediction_id=str(created["_id"]),
                        stockout_probability=float(created["stockout_probability"]),
                        risk_level=created["risk_level"],
                        item_name=item["item_name"],
                    )
                )

        except MLInferenceException:
            failed += 1
        except Exception:
            failed += 1

    return BatchPredictResponse(
        total_items=len(items),
        succeeded=succeeded,
        failed=failed,
        high_risk_count=high_risk_count,
        critical_count=critical_count,
    )


async def get_predictions(
    db: AsyncIOMotorDatabase,
    filters: PredictionFilter,
) -> Tuple[List[RealtimePredictResponse], int]:
    page, limit = validate_pagination(filters.page, filters.limit)

    predictions, total = await prediction_repository.get_all(
        db=db,
        page=page,
        limit=limit,
        filters=filters.model_dump(exclude_none=True),
    )

    return [to_prediction_response(prediction) for prediction in predictions], total


async def get_prediction_by_id(
    db: AsyncIOMotorDatabase,
    id: str,
) -> RealtimePredictResponse:
    prediction = await prediction_repository.get_by_id(db, id)
    if not prediction:
        raise NotFoundException("Prediction not found")

    return to_prediction_response(prediction)


async def get_latest_for_item(
    db: AsyncIOMotorDatabase,
    item_id: str,
    facility_id: str,
) -> RealtimePredictResponse:
    prediction = await prediction_repository.get_latest_for_item(
        db=db,
        item_id=item_id,
        facility_id=facility_id,
    )

    if not prediction:
        raise NotFoundException("Prediction not found")

    return to_prediction_response(prediction)