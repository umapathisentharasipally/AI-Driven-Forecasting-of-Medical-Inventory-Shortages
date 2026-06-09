from __future__ import annotations

import argparse

from src.training.train_xgboost import train_xgboost
from src.training.train_anomaly_model import train_anomaly_model
from src.training.train_prophet import train_prophet
from src.utils.metrics import save_json
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelTrainingError
from src.utils.logger import get_logger

logger = get_logger(__name__)



@log_and_raise("Training pipeline failed", ModelTrainingError)
def run_training_pipeline(
    xgboost_config: str = "configs/xgboost_config.yaml",
    anomaly_config: str = "configs/anomaly_config.yaml",
    prophet_config: str = "configs/prophet_config.yaml",
    skip_forecast: bool = False,
    skip_anomaly: bool = False,
) -> dict:
    results = {"xgboost": train_xgboost(xgboost_config)}

    if not skip_anomaly:
        results["anomaly"] = train_anomaly_model(anomaly_config)

    if not skip_forecast:
        results["prophet"] = train_prophet(prophet_config)

    save_json(results, "artifacts/training_pipeline_report.json")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--xgboost-config", default="configs/xgboost_config.yaml")
    parser.add_argument("--anomaly-config", default="configs/anomaly_config.yaml")
    parser.add_argument("--prophet-config", default="configs/prophet_config.yaml")
    parser.add_argument("--skip-forecast", action="store_true")
    parser.add_argument("--skip-anomaly", action="store_true")
    args = parser.parse_args()
    print(run_training_pipeline(args.xgboost_config, args.anomaly_config, args.prophet_config, args.skip_forecast, args.skip_anomaly))
