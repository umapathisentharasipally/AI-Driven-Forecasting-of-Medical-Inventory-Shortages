from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler.daily_prediction_job import run_daily_predictions
from app.scheduler.daily_report_job import run_daily_report
from app.scheduler.expiry_check_job import run_expiry_check
from app.scheduler.export_cleanup_job import run_export_cleanup
from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def _run_logged(job_name: str, job_func):
    start = utc_now()
    logger.info(f"{job_name} started")

    try:
        await job_func()
        duration_ms = round((utc_now() - start).total_seconds() * 1000, 2)
        logger.info(f"{job_name} completed duration_ms={duration_ms}")
    except Exception as exc:
        duration_ms = round((utc_now() - start).total_seconds() * 1000, 2)
        logger.error(f"{job_name} failed duration_ms={duration_ms} error={exc}")


def init_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone="UTC",
        job_defaults={
            "misfire_grace_time": 3600,
            "coalesce": True,
            "max_instances": 1,
        },
    )

    scheduler.add_job(
        _run_logged,
        CronTrigger(hour=2, minute=0, timezone="UTC"),
        args=["daily_predictions", run_daily_predictions],
        id="daily_predictions",
        name="daily_predictions",
        misfire_grace_time=3600,
        replace_existing=True,
    )

    scheduler.add_job(
        _run_logged,
        CronTrigger(hour=3, minute=0, timezone="UTC"),
        args=["daily_report", run_daily_report],
        id="daily_report",
        name="daily_report",
        misfire_grace_time=3600,
        replace_existing=True,
    )

    scheduler.add_job(
        _run_logged,
        CronTrigger(hour=6, minute=0, timezone="UTC"),
        args=["expiry_check", run_expiry_check],
        id="expiry_check",
        name="expiry_check",
        misfire_grace_time=3600,
        replace_existing=True,
    )

    scheduler.add_job(
        _run_logged,
        CronTrigger(hour=1, minute=0, timezone="UTC"),
        args=["export_cleanup", run_export_cleanup],
        id="export_cleanup",
        name="export_cleanup",
        misfire_grace_time=3600,
        replace_existing=True,
    )

    return scheduler


def start(scheduler: AsyncIOScheduler) -> None:
    if scheduler and not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


def shutdown(scheduler: AsyncIOScheduler) -> None:
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shutdown complete")