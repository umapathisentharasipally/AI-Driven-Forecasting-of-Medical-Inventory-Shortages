from __future__ import annotations
from asyncio import constants

import pandas as pd

from ..utils.constants import DATE_COLUMN, TARGET_COLUMN
from ..utils.exceptions import DataValidationError
from ..utils.logger import get_logger, log_exception

logger = get_logger(__name__)

BOOL_MAP = {"yes": 1, "true": 1, "1": 1, "y": 1, "no": 0, "false": 0, "0": 0, "n": 0}
BOOLEAN_COLUMNS = [
    "recent_usage_spike",
    "active_po_in_transit",
    "sole_source_item",
    "substitution_available",
    "pandemic_or_surge_flag",
]


def clean_inventory_data(df: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    """Clean schema-safe inventory data for training and inference."""
    try:
        if df is None or not isinstance(df, pd.DataFrame):
            raise DataValidationError("clean_inventory_data expected a pandas DataFrame")
        data = df.copy()
        data.columns = [c.strip() for c in data.columns]

        if DATE_COLUMN in data.columns:
            data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN], errors="coerce")

        object_cols = data.select_dtypes(include="object").columns
        for col in object_cols:
            data[col] = data[col].astype("string").str.strip()

        for col in BOOLEAN_COLUMNS:
            if col in data.columns:
                lowered = data[col].astype("string").str.lower().str.strip()
                mapped = lowered.map(BOOL_MAP)
                if mapped.notna().any():
                    data[col] = mapped.fillna(data[col])

        if require_target and TARGET_COLUMN in data.columns:
            data[TARGET_COLUMN] = pd.to_numeric(data[TARGET_COLUMN], errors="coerce").fillna(0).astype(int)

        duplicate_count = int(data.duplicated().sum())
        if duplicate_count:
            logger.info("Removed duplicate rows: %s", duplicate_count)
        data = data.drop_duplicates().reset_index(drop=True)
        logger.info("Data cleaning completed: rows=%s columns=%s", data.shape[0], data.shape[1])
        return data
    except DataValidationError:
        raise
    except Exception as exc:
        log_exception(logger, "Data cleaning failed", exc)
        raise DataValidationError("Data cleaning failed") from exc
