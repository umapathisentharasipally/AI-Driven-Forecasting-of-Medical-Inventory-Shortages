from __future__ import annotations

import pandas as pd

from ..utils.constants import DATE_COLUMN, TARGET_COLUMN
from ..utils.exceptions import DataValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = {
    "record_id", "snapshot_date", "facility_id", "facility_type", "department",
    "item_id", "item_category", "item_subcategory", "criticality_level",
    "unit_of_measure", "shelf_life_days", "avg_daily_usage_last_30d",
    "avg_daily_usage_last_90d", "usage_cv_last_90d", "demand_trend",
    "seasonal_demand_factor", "recent_usage_spike", "current_stock_on_hand",
    "safety_stock_level", "days_of_supply_on_hand", "stock_as_pct_of_safety_level",
    "reorder_point_days", "days_until_next_scheduled_order", "primary_vendor_id",
    "vendor_reliability_score", "contracted_lead_time_days", "actual_avg_lead_time_last_6m",
    "lead_time_variability_days", "active_po_in_transit", "backorder_frequency_last_12m",
    "sole_source_item", "substitution_available", "facility_census_pct",
    "pandemic_or_surge_flag", "days_since_last_stockout", "stockout_event",
}


def validate_inventory_schema(df: pd.DataFrame, require_target: bool = True) -> None:
    """Validate medical inventory schema before training or inference."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise DataValidationError("Input must be a pandas DataFrame")
    if df.empty:
        raise DataValidationError("Input DataFrame is empty")

    expected = set(REQUIRED_COLUMNS)
    if not require_target:
        expected.discard(TARGET_COLUMN)

    missing = sorted(expected - set(df.columns))
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")

    if DATE_COLUMN in df.columns and df[DATE_COLUMN].isna().all():
        raise DataValidationError("snapshot_date exists but all values failed datetime parsing")

    if require_target:
        values = set(df[TARGET_COLUMN].dropna().unique())
        valid_values = {0, 1, "0", "1","False", "True", "false", "true", "no", "yes", "n", "y"}
        if not values.issubset(valid_values):
            raise DataValidationError(f"stockout_event must be binary. Found values: {sorted(map(str, values))}")

    logger.info("Schema validation passed: rows=%s columns=%s require_target=%s", df.shape[0], df.shape[1], require_target)
