import pandas as pd
from .feature_engineering import safe_divide


def build_anomaly_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if {"avg_daily_usage_last_30d", "avg_daily_usage_last_90d"}.issubset(data.columns):
        data["usage_ratio_30_90"] = safe_divide(data["avg_daily_usage_last_30d"], data["avg_daily_usage_last_90d"], default=1.0)
    if {"current_stock_on_hand", "safety_stock_level"}.issubset(data.columns):
        data["stock_to_safety_ratio"] = safe_divide(data["current_stock_on_hand"], data["safety_stock_level"], default=1.0)
    if {"actual_avg_lead_time_last_6m", "contracted_lead_time_days"}.issubset(data.columns):
        data["lead_time_ratio"] = safe_divide(data["actual_avg_lead_time_last_6m"], data["contracted_lead_time_days"], default=1.0)
    return data
