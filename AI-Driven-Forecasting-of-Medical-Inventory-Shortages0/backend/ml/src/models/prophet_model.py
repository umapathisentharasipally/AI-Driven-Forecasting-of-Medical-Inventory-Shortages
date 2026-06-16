from __future__ import annotations
import pandas as pd


def build_prophet_model(params: dict):
    try:
        from prophet import Prophet
    except ImportError as exc:
        raise ImportError("Prophet is not installed. Install it with: pip install prophet") from exc
    return Prophet(**params)


def prepare_prophet_frame(df: pd.DataFrame, date_col: str, target_col: str) -> pd.DataFrame:
    data = df[[date_col, target_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data[target_col] = pd.to_numeric(data[target_col], errors="coerce")
    data = data.dropna(subset=[date_col, target_col])
    daily = data.groupby(date_col)[target_col].mean().reset_index()
    return daily.rename(columns={date_col: "ds", target_col: "y"}).sort_values("ds")


def forecast_with_prophet(model, periods: int, freq: str = "D") -> pd.DataFrame:
    future = model.make_future_dataframe(periods=periods, freq=freq)
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
