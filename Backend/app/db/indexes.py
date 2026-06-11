from pymongo import ASCENDING, DESCENDING

from app.config.database import get_database
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_all_indexes() -> None:
    db = await get_database()

    await db["users"].create_index([("email", ASCENDING)], unique=True)
    await db["users"].create_index([("role_id", ASCENDING)])
    await db["users"].create_index([("is_active", ASCENDING)])

    await db["inventory_items"].create_index(
        [("item_id", ASCENDING), ("facility_id", ASCENDING)],
        unique=True,
    )
    await db["inventory_items"].create_index([("vendor_id", ASCENDING)])
    await db["inventory_items"].create_index(
        [("category", ASCENDING), ("is_critical", ASCENDING)]
    )
    await db["inventory_items"].create_index(
        [
            ("current_stock_on_hand", ASCENDING),
            ("safety_stock_level", ASCENDING),
        ]
    )
    await db["inventory_items"].create_index([("department_tags", ASCENDING)])
    await db["inventory_items"].create_index([("expiry_date", ASCENDING)])

    await db["vendors"].create_index([("vendor_code", ASCENDING)], unique=True)
    await db["vendors"].create_index([("is_active", ASCENDING)])

    await db["predictions"].create_index(
        [
            ("item_id", ASCENDING),
            ("facility_id", ASCENDING),
            ("prediction_date", ASCENDING),
        ]
    )
    await db["predictions"].create_index(
        [("risk_level", ASCENDING), ("prediction_date", ASCENDING)]
    )
    await db["predictions"].create_index([("stockout_probability", DESCENDING)])
    await db["predictions"].create_index(
        [("created_at", ASCENDING)],
        expireAfterSeconds=90 * 24 * 60 * 60,
    )

    await db["anomalies"].create_index(
        [("item_id", ASCENDING), ("detected_at", ASCENDING)]
    )
    await db["anomalies"].create_index(
        [("is_acknowledged", ASCENDING), ("anomaly_score", ASCENDING)]
    )

    await db["alerts"].create_index(
        [("status", ASCENDING), ("severity", ASCENDING), ("created_at", ASCENDING)]
    )
    await db["alerts"].create_index([("item_id", ASCENDING), ("status", ASCENDING)])

    await db["notifications"].create_index(
        [("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", ASCENDING)]
    )
    await db["notifications"].create_index(
        [("created_at", ASCENDING)],
        expireAfterSeconds=30 * 24 * 60 * 60,
    )

    await db["audit_logs"].create_index(
        [("user_id", ASCENDING), ("created_at", ASCENDING)]
    )
    await db["audit_logs"].create_index(
        [("resource_type", ASCENDING), ("resource_id", ASCENDING)]
    )
    await db["audit_logs"].create_index(
        [("created_at", ASCENDING)],
        expireAfterSeconds=365 * 24 * 60 * 60,
    )

    await db["consumption_logs"].create_index(
        [("item_id", ASCENDING), ("consumed_at", DESCENDING)]
    )
    await db["consumption_logs"].create_index(
        [("facility_id", ASCENDING), ("consumed_at", ASCENDING)]
    )
    await db["consumption_logs"].create_index(
        [("created_at", ASCENDING)],
        expireAfterSeconds=2 * 365 * 24 * 60 * 60,
    )

    logger.info("All MongoDB indexes created successfully")