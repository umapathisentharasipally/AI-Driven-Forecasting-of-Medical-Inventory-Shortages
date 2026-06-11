import numpy as np
import pandas as pd


def safe_divide(numerator: pd.Series, denominator: pd.Series | float | int, default: float = 0.0) -> pd.Series:
    if isinstance(denominator, (int, float, np.integer, np.floating)):
        denominator_value = float(denominator)
        denominator_value = np.nan if denominator_value == 0 else denominator_value
        result = numerator.astype(float) / denominator_value
    else:
        result = numerator.astype(float) / denominator.replace(0, np.nan).astype(float)
    return result.replace([np.inf, -np.inf], np.nan).fillna(default)


def add_inventory_features(df: pd.DataFrame) -> pd.DataFrame:
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
        data["vendor_risk_score"] = (1 - data["vendor_reliability_score"].astype(float).clip(0, 1)) + safe_divide(data["backorder_frequency_last_12m"], data["backorder_frequency_last_12m"].max() or 1)
    return data
