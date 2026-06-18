import pandas as pd


def add_date_features(df: pd.DataFrame, date_col: str = "snapshot_date") -> pd.DataFrame:
    data = df.copy()
    if date_col not in data.columns:
        return data
    dates = pd.to_datetime(data[date_col], errors="coerce")
    data["snapshot_year"] = dates.dt.year
    data["snapshot_month"] = dates.dt.month
    data["snapshot_quarter"] = dates.dt.quarter
    data["snapshot_dayofweek"] = dates.dt.dayofweek
    data["snapshot_is_month_end"] = dates.dt.is_month_end.astype(int)
    return data


def build_daily_stockout_rate(df: pd.DataFrame, date_col: str = "snapshot_date", target_col: str = "stockout_event") -> pd.DataFrame:
    data = df[[date_col, target_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data.dropna(subset=[date_col])
    daily = data.groupby(date_col)[target_col].mean().reset_index(name="stockout_rate")
    return daily.sort_values(date_col).reset_index(drop=True)


def add_lag_rolling_features(ts_df: pd.DataFrame, date_col: str, target_col: str) -> pd.DataFrame:
    data = ts_df[[date_col, target_col]].copy().sort_values(date_col)
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data["dayofweek"] = data[date_col].dt.dayofweek
    data["month"] = data[date_col].dt.month
    data["quarter"] = data[date_col].dt.quarter
    for lag in [1, 2, 3, 7, 14, 30]:
        data[f"lag_{lag}"] = data[target_col].shift(lag)
    for window in [3, 7, 14, 30]:
        shifted = data[target_col].shift(1)
        data[f"rolling_mean_{window}"] = shifted.rolling(window).mean()
        data[f"rolling_std_{window}"] = shifted.rolling(window).std()
    return data.dropna().reset_index(drop=True)
