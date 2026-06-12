from pathlib import Path

from app.utils.date_utils import utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_export_cleanup() -> None:
    try:
        now_ts = utc_now().timestamp()
        exports_deleted = 0
        reports_deleted = 0

        export_dir = Path("exports")
        report_dir = Path("reports")

        if export_dir.exists():
            for file_path in export_dir.iterdir():
                if file_path.is_file():
                    age_seconds = now_ts - file_path.stat().st_mtime
                    if age_seconds > 24 * 60 * 60:
                        file_path.unlink(missing_ok=True)
                        exports_deleted += 1

        if report_dir.exists():
            for file_path in report_dir.iterdir():
                if file_path.is_file():
                    age_seconds = now_ts - file_path.stat().st_mtime
                    if age_seconds > 7 * 24 * 60 * 60:
                        file_path.unlink(missing_ok=True)
                        reports_deleted += 1

        logger.info(
            f"export_cleanup completed exports_deleted={exports_deleted} "
            f"reports_deleted={reports_deleted}"
        )

    except Exception as exc:
        logger.error(f"export_cleanup job failed: {exc}")