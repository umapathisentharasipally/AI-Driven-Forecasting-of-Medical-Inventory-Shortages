from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def create_lstm_sequences(values: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for idx in range(lookback, len(values)):
        X.append(values[idx - lookback:idx])
        y.append(values[idx])
    return np.asarray(X), np.asarray(y)


def build_lstm_model(lookback: int, units: int = 64, dropout: float = 0.2):
    try:
        import importlib
        keras = importlib.import_module("tensorflow.keras")
        Sequential = keras.Sequential
        Dense = keras.layers.Dense
        Dropout = keras.layers.Dropout
        LSTM = keras.layers.LSTM
    except ImportError as exc:
        raise ImportError("TensorFlow is not installed. Install it with: pip install tensorflow") from exc
    model = Sequential([
        LSTM(units, input_shape=(lookback, 1)),
        Dropout(dropout),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def prepare_univariate_series(df: pd.DataFrame, date_col: str, target_col: str) -> pd.DataFrame:
    data = df[[date_col, target_col]].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data[target_col] = pd.to_numeric(data[target_col], errors="coerce")
    data = data.dropna(subset=[date_col, target_col])
    return data.groupby(date_col)[target_col].mean().reset_index().sort_values(date_col)


def scale_series(values: np.ndarray) -> tuple[np.ndarray, MinMaxScaler]:
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(values.reshape(-1, 1))
    return scaled, scaler
