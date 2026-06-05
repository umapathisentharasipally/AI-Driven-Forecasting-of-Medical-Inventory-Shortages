import pandas as pd
from .feature_engineering import add_inventory_features
from .trend_features import add_date_features
from .anomaly_features import build_anomaly_features


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    data = add_inventory_features(df)
    data = add_date_features(data)
    data = build_anomaly_features(data)
    return data
