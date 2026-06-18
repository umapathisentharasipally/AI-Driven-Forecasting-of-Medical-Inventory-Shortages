from datetime import timedelta

from app.config.database import connect_db, get_database
from app.repositories.alert_repository import find_existing_open
from app.services import alert_service
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_expiry_check() -> None:
    start = utc_now()
    items_checked = 0
    alerts_created = 0
    skipped_duplicates = 0

    try:
        await connect_db()
        db = await get_database()

        now = utc_now()
        cutoff = now + timedelta(days=30)

        items = await db["inventory_items"].find(
            {
                "is_active": True,
                "expiry_date": {
                    "$gt": now,
                    "$lte": cutoff,
                },
            }
        ).to_list(length=None)

        items_checked = len(items)

        for item in items:
            duplicate = await find_existing_open(
                db=db,
                item_id=item["item_id"],
                facility_id=item["facility_id"],
                alert_type="expiry",
            )

            if duplicate:
                skipped_duplicates += 1
                continue

            created = await alert_service.create_expiry_alert(
                db=db,
                item_id=item["item_id"],
                facility_id=item["facility_id"],
                inventory_doc_id=str(item["_id"]),
                expiry_date=item["expiry_date"],
                item_name=item["item_name"],
            )

            if created:
                alerts_created += 1

        duration_ms = round((utc_now() - start).total_seconds() * 1000, 2)

        logger.info(
            f"expiry_check completed items_checked={items_checked} "
            f"alerts_created={alerts_created} skipped_duplicates={skipped_duplicates} "
            f"duration_ms={duration_ms}"
        )

    except Exception as exc:
        logger.error(f"expiry_check job failed: {exc}")