from app.config.database import connect_db, get_database
from app.config.settings import settings
from app.core.exception_handler import MLInferenceException
from app.repositories import prediction_repository
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger
import json
from pathlib import Path
logger = get_logger(__name__)

ML_FIELDS = [
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


def _build_record(item: dict) -> dict:
    missing = [field for field in ML_FIELDS if field not in item]
    if missing:
        raise ValueError(f"Missing ML fields: {missing}")

    return {field: item[field] for field in ML_FIELDS}

async def run_daily_predictions() -> None:
    start = utc_now()
    total = 0
    predicted = 0
    skipped = 0
    failed = 0

    try:
        await connect_db()
        db = await get_database()

        from ml.src.inference.realtime_predict import RealtimeStockoutPredictor

        predictor = RealtimeStockoutPredictor(
            config_path=f"{settings.ML_CONFIGS_PATH}/xgboost_config.yaml",
            risk_config_path=f"{settings.ML_CONFIGS_PATH}/risk_engine_config.yaml",
        )

        items = await db["inventory_items"].find({"is_active": True}).to_list(length=None)
        total = len(items)

        prediction_docs = []

        for item in items:
            inventory_doc_id = str(item["_id"])

            if await prediction_repository.already_predicted_today(db, inventory_doc_id):
                skipped += 1
                continue

            try:
                record = _build_record(item)
                result = predictor.predict_one(record)
                now = utc_now()

                prediction_docs.append(
                    {
                        "item_id": item["item_id"],
                        "facility_id": item["facility_id"],
                        "inventory_doc_id": inventory_doc_id,
                        "model_name": "xgboost",
                        "model_version": _load_model_version(),                        "prediction_date": now,
                        "stockout_probability": float(result["stockout_probability"]),
                        "stockout_prediction": int(result["stockout_prediction"]),
                        "risk_level": result["risk_level"],
                        "days_of_supply_on_hand": float(item["days_of_supply_on_hand"]),
                        "feature_snapshot": record,
                        "created_at": now,
                    }
                )

            except MLInferenceException:
                failed += 1
            except Exception as exc:
                failed += 1
                logger.error(f"Daily prediction failed for item {inventory_doc_id}: {exc}")

        predicted = await prediction_repository.bulk_create(db, prediction_docs)
        duration_ms = round((utc_now() - start).total_seconds() * 1000, 2)

        await db["daily_run_logs"].insert_one(
            {
                "date": start.date().isoformat(),
                "job_name": "daily_predictions",
                "total": total,
                "predicted": predicted,
                "skipped": skipped,
                "failed": failed,
                "duration_ms": duration_ms,
                "created_at": utc_now(),
            }
        )

        logger.info(
            f"daily_predictions completed total={total} predicted={predicted} "
            f"skipped={skipped} failed={failed} duration_ms={duration_ms}"
        )

    except Exception as exc:
        logger.error(f"daily_predictions job failed: {exc}")
def _load_model_version() -> str:
    metadata_path = Path(settings.ML_ARTIFACTS_PATH) / "model_metadata.json"

    try:
        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as file:
                metadata = json.load(file)
                return str(
                    metadata.get("model_version")
                    or metadata.get("version")
                    or "unknown"
                )
    except Exception as exc:
        logger.error(f"Failed to read model metadata: {exc}")

    return "unknown"