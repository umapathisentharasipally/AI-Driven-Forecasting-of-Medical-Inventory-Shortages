from datetime import timedelta

from app.config.database import connect_db, get_database
from app.services import report_service
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_daily_report() -> None:
    try:
        await connect_db()
        db = await get_database()

        end = utc_now()
        start = end - timedelta(days=1)

        report = await report_service.generate_daily_summary(
            db=db,
            period_start=start,
            period_end=end,
            user_id=None,
        )

        logger.info(f"daily_report scheduled generation started report_id={report.id}")

    except Exception as exc:
        logger.error(f"daily_report job failed: {exc}")