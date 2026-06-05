from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..utils.constants import DATE_COLUMN
from ..utils.exceptions import DataLoadError
from ..utils.logger import get_logger, log_exception

logger = get_logger(__name__)


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file and parse snapshot_date when present."""
    csv_path = Path(path)
    try:
        if not csv_path.exists():
            raise DataLoadError(f"CSV file not found: {csv_path}")
        if csv_path.suffix.lower() != ".csv":
            raise DataLoadError(f"Expected a .csv file, got: {csv_path}")
        df = pd.read_csv(csv_path)
        if df.empty:
            raise DataLoadError(f"CSV file is empty: {csv_path}")
        if DATE_COLUMN in df.columns:
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")
        logger.info("Loaded CSV: path=%s rows=%s columns=%s", csv_path, df.shape[0], df.shape[1])
        return df
    except DataLoadError:
        raise
    except Exception as exc:
        log_exception(logger, f"Failed to load CSV: {csv_path}", exc)
        raise DataLoadError(f"Failed to load CSV: {csv_path}") from exc


def save_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Save a DataFrame to CSV with directory creation and logging."""
    csv_path = Path(path)
    try:
        if df is None or not isinstance(df, pd.DataFrame):
            raise DataLoadError("save_csv expected a pandas DataFrame")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        logger.info("Saved CSV: path=%s rows=%s columns=%s", csv_path, df.shape[0], df.shape[1])
    except DataLoadError:
        raise
    except Exception as exc:
        log_exception(logger, f"Failed to save CSV: {csv_path}", exc)
        raise DataLoadError(f"Failed to save CSV: {csv_path}") from exc
