from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils.exceptions import FeatureEngineeringError
from ..utils.logger import get_logger, log_exception

logger = get_logger(__name__)


def safe_divide(numerator: pd.Series, denominator: pd.Series, default: float = 0.0) -> pd.Series:
    result = numerator.astype(float) / denominator.replace(0, np.nan).astype(float)
    return result.replace([np.inf, -np.inf], np.nan).fillna(default)


def add_inventory_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create stockout-focused features from raw inventory columns."""
    try:
        if df is None or not isinstance(df, pd.DataFrame):
            raise FeatureEngineeringError("add_inventory_features expected a pandas DataFrame")
        data = df.copy()
        if {"current_stock_on_hand", "safety_stock_level"}.issubset(data.columns):
            data["stock_gap"] = data["current_stock_on_hand"] - data["safety_stock_level"]
            data["stock_gap_pct"] = safe_divide(data["stock_gap"], data["safety_stock_level"])
            data["below_safety_stock"] = (data["current_stock_on_hand"] < data["safety_stock_level"]).astype(int)
        if {"current_stock_on_hand", "avg_daily_usage_last_30d"}.issubset(data.columns):
            data["estimated_days_until_empty"] = safe_divide(data["current_stock_on_hand"], data["avg_daily_usage_last_30d"])
        if {"avg_daily_usage_last_30d", "avg_daily_usage_last_90d"}.issubset(data.columns):
            data["usage_change_30d_vs_90d"] = data["avg_daily_usage_last_30d"] - data["avg_daily_usage_last_90d"]
            data["usage_change_pct_30d_vs_90d"] = safe_divide(data["usage_change_30d_vs_90d"], data["avg_daily_usage_last_90d"])
        if {"days_until_next_scheduled_order", "days_of_supply_on_hand"}.issubset(data.columns):
            data["will_run_out_before_order"] = (data["days_of_supply_on_hand"] < data["days_until_next_scheduled_order"]).astype(int)
        if {"avg_daily_usage_last_30d", "days_until_next_scheduled_order", "current_stock_on_hand"}.issubset(data.columns):
            projected_usage = data["avg_daily_usage_last_30d"] * data["days_until_next_scheduled_order"]
            data["projected_stock_at_next_order"] = data["current_stock_on_hand"] - projected_usage
        if {"actual_avg_lead_time_last_6m", "contracted_lead_time_days"}.issubset(data.columns):
            data["lead_time_delay_days"] = data["actual_avg_lead_time_last_6m"] - data["contracted_lead_time_days"]
            data["lead_time_delay_pct"] = safe_divide(data["lead_time_delay_days"], data["contracted_lead_time_days"])
        if {"vendor_reliability_score", "backorder_frequency_last_12m"}.issubset(data.columns):
            max_backorder = data["backorder_frequency_last_12m"].max()
            data["vendor_risk_score"] = (1 - data["vendor_reliability_score"].astype(float).clip(0, 1)) + safe_divide(data["backorder_frequency_last_12m"], max_backorder or 1)
        logger.info("Inventory features created: input_columns=%s output_columns=%s", df.shape[1], data.shape[1])
        return data
    except FeatureEngineeringError:
        raise
    except Exception as exc:
        log_exception(logger, "Feature engineering failed", exc)
        raise FeatureEngineeringError("Feature engineering failed") from exc
