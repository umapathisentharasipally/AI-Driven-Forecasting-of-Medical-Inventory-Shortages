from __future__ import annotations
import argparse
from pathlib import Path
from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv
from src.models.lstm_model import build_lstm_model, create_lstm_sequences, prepare_univariate_series, scale_series
from src.utils.save_load_model import save_object
from src.utils.config import load_yaml_config
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelTrainingError


@log_and_raise("LSTM training failed", ModelTrainingError)
def train_lstm(config_path: str = "configs/prophet_config.yaml", lookback: int = 30, epochs: int = 20, batch_size: int = 32) -> dict:
    config = load_yaml_config(config_path, required_keys=["paths", "date_column", "target_column"])
    df = clean_inventory_data(load_csv(config["paths"]["raw_data"]), require_target=False)
    series = prepare_univariate_series(df, config["date_column"], config["target_column"])
    if len(series) <= lookback + 10:
        raise ModelTrainingError("Not enough observations to train LSTM")
    scaled, scaler = scale_series(series[config["target_column"]].to_numpy())
    X, y = create_lstm_sequences(scaled, lookback)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    model = build_lstm_model(lookback=lookback)
    history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=epochs, batch_size=batch_size, verbose=1)
    model_path = Path("artifacts/lstm_model.keras")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    save_object(scaler, "artifacts/lstm_scaler.pkl")
    return {"model_path": str(model_path), "final_val_loss": float(history.history["val_loss"][-1]), "lookback": lookback}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/prophet_config.yaml")
    parser.add_argument("--lookback", type=int, default=30)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    print(train_lstm(args.config, args.lookback, args.epochs, args.batch_size))
