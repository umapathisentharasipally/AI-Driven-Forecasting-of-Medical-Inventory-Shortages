import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.config.settings import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    enqueue=True,
    backtrace=settings.APP_ENV == "development",
    diagnose=settings.APP_ENV == "development",
)

logger.add(
    LOG_DIR / "app.log",
    level=settings.LOG_LEVEL,
    rotation="1 day",
    retention="30 days",
    enqueue=True,
    backtrace=False,
    diagnose=False,
)

logger.add(
    LOG_DIR / "error.log",
    level="ERROR",
    rotation="1 week",
    retention="30 days",
    enqueue=True,
    backtrace=False,
    diagnose=False,
)


def get_logger(name: str):
    return logger.bind(module=name)


def log_request(
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    user_id: str | None = None,
) -> None:
    logger.bind(
        method=method,
        path=path,
        status_code=status,
        duration_ms=duration_ms,
        user_id=user_id,
    ).info(
        f"{method} {path} completed with {status} in {duration_ms}ms"
    )


def log_ml_inference(
    model_name: str,
    item_id: str,
    result: Any,
    duration_ms: float,
) -> None:
    logger.bind(
        model_name=model_name,
        item_id=item_id,
        result=result,
        duration_ms=duration_ms,
    ).info(
        f"ML inference completed for {item_id} using {model_name} in {duration_ms}ms"
    )