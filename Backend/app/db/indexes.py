from pymongo import ASCENDING, DESCENDING

from app.config.database import get_database
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_all_indexes() -> None:
    db = await get_database()

    try:
        # Users
        await db["users"].create_index(
            [("email", ASCENDING)],
            unique=True,
        )
        await db["users"].create_index(
            [("role_id", ASCENDING)],
        )
        await db["users"].create_index(
            [("is_active", ASCENDING)],
        )

        # Roles
        await db["roles"].create_index(
            [("name", ASCENDING)],
            unique=True,
        )

        # Inventory Items
        await db["inventory_items"].create_index(
            [("item_id", ASCENDING), ("facility_id", ASCENDING)],
            unique=True,
        )
        await db["inventory_items"].create_index(
            [("vendor_id", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("item_name", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("category", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("category", ASCENDING), ("is_critical", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("is_critical", ASCENDING), ("current_stock_on_hand", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("current_stock_on_hand", ASCENDING), ("safety_stock_level", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("department_tags", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("expiry_date", ASCENDING)],
        )
        await db["inventory_items"].create_index(
            [("is_active", ASCENDING), ("expiry_date", ASCENDING)],
        )

        # Vendors
        await db["vendors"].create_index(
            [("vendor_code", ASCENDING)],
            unique=True,
        )
        await db["vendors"].create_index(
            [("is_active", ASCENDING)],
        )

        # Predictions
        await db["predictions"].create_index(
            [
                ("item_id", ASCENDING),
                ("facility_id", ASCENDING),
                ("prediction_date", DESCENDING),
            ]
        )
        await db["predictions"].create_index(
            [("risk_level", ASCENDING), ("prediction_date", DESCENDING)],
        )
        await db["predictions"].create_index(
            [("prediction_date", DESCENDING), ("risk_level", ASCENDING)],
        )
        await db["predictions"].create_index(
            [("stockout_probability", DESCENDING)],
        )
        await db["predictions"].create_index(
            [("inventory_doc_id", ASCENDING), ("prediction_date", DESCENDING)],
        )
        await db["predictions"].create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=90 * 24 * 60 * 60,
        )

        # Anomalies
        await db["anomalies"].create_index(
            [("item_id", ASCENDING), ("detected_at", DESCENDING)],
        )
        await db["anomalies"].create_index(
            [("is_acknowledged", ASCENDING), ("anomaly_score", DESCENDING)],
        )
        await db["anomalies"].create_index(
            [("detected_at", DESCENDING), ("is_acknowledged", ASCENDING)],
        )
        await db["anomalies"].create_index(
            [("facility_id", ASCENDING), ("detected_at", DESCENDING)],
        )

        # Trends
        await db["trends"].create_index(
            [
                ("item_id", ASCENDING),
                ("facility_id", ASCENDING),
                ("period", ASCENDING),
            ],
            unique=True,
        )
        await db["trends"].create_index(
            [("computed_at", DESCENDING)],
        )

        # Alerts
        await db["alerts"].create_index(
            [("status", ASCENDING), ("severity", ASCENDING), ("created_at", DESCENDING)],
        )
        await db["alerts"].create_index(
            [("severity", ASCENDING), ("status", ASCENDING)],
        )
        await db["alerts"].create_index(
            [("item_id", ASCENDING), ("status", ASCENDING)],
        )
        await db["alerts"].create_index(
            [
                ("item_id", ASCENDING),
                ("facility_id", ASCENDING),
                ("alert_type", ASCENDING),
                ("status", ASCENDING),
            ]
        )
        await db["alerts"].create_index(
            [("assigned_to", ASCENDING), ("status", ASCENDING)],
        )
        await db["alerts"].create_index(
            [("created_at", DESCENDING)],
        )

        # Notifications
        await db["notifications"].create_index(
            [("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", DESCENDING)],
        )
        await db["notifications"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
        )
        await db["notifications"].create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=30 * 24 * 60 * 60,
        )

        # Reports
        await db["reports"].create_index(
            [("report_type", ASCENDING)],
        )
        await db["reports"].create_index(
            [("status", ASCENDING)],
        )
        await db["reports"].create_index(
            [("created_at", DESCENDING)],
        )
        await db["reports"].create_index(
            [("generated_by", ASCENDING), ("created_at", DESCENDING)],
        )

        # Audit Logs
        await db["audit_logs"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
        )
        await db["audit_logs"].create_index(
            [("resource_type", ASCENDING), ("resource_id", ASCENDING)],
        )
        await db["audit_logs"].create_index(
            [("action", ASCENDING), ("created_at", DESCENDING)],
        )
        await db["audit_logs"].create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=365 * 24 * 60 * 60,
        )

        # Consumption Logs
        await db["consumption_logs"].create_index(
            [("item_id", ASCENDING), ("consumed_at", DESCENDING)],
        )
        await db["consumption_logs"].create_index(
            [("facility_id", ASCENDING), ("consumed_at", ASCENDING)],
        )
        await db["consumption_logs"].create_index(
            [("department", ASCENDING), ("consumed_at", DESCENDING)],
        )
        await db["consumption_logs"].create_index(
            [("created_at", ASCENDING)],
            expireAfterSeconds=2 * 365 * 24 * 60 * 60,
        )

        # Daily Scheduler Run Logs
        await db["daily_run_logs"].create_index(
            [("date", ASCENDING), ("job_name", ASCENDING)],
        )
        await db["daily_run_logs"].create_index(
            [("created_at", DESCENDING)],
        )

        logger.info("All MongoDB indexes created successfully")

    except Exception as exc:
        logger.exception(f"MongoDB index creation failed: {exc}")
        raise