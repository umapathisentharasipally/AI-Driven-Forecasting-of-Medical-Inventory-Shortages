from __future__ import annotations

import argparse

from src.training.train_prophet import train_prophet
from src.training.train_lstm import train_lstm
from src.utils.metrics import save_json
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelTrainingError
from src.utils.logger import get_logger

logger = get_logger(__name__)



@log_and_raise("Forecast pipeline failed", ModelTrainingError)
def run_forecast_pipeline(
    prophet_config: str = "configs/prophet_config.yaml",
    train_lstm_model: bool = False,
    lookback: int = 30,
    epochs: int = 20,
    batch_size: int = 32,
) -> dict:
    results = {"prophet": train_prophet(prophet_config)}
    if train_lstm_model:
        results["lstm"] = train_lstm(prophet_config, lookback=lookback, epochs=epochs, batch_size=batch_size)
    save_json(results, "artifacts/forecast_pipeline_report.json")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prophet-config", default="configs/prophet_config.yaml")
    parser.add_argument("--train-lstm", action="store_true")
    parser.add_argument("--lookback", type=int, default=30)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    print(run_forecast_pipeline(args.prophet_config, args.train_lstm, args.lookback, args.epochs, args.batch_size))
