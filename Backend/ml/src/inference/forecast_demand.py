from __future__ import annotations

import argparse

from src.data.data_loader import save_csv
from src.models.prophet_model import forecast_with_prophet
from src.utils.config import load_yaml_config
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelInferenceError
from src.utils.logger import get_logger
from src.utils.save_load_model import load_object

logger = get_logger(__name__)


@log_and_raise("Demand forecast inference failed", ModelInferenceError)
def forecast_demand(config_path: str = "configs/prophet_config.yaml"):
    config = load_yaml_config(config_path, required_keys=["paths", "forecast_periods"])
    model = load_object(config["paths"]["model"])
    forecast = forecast_with_prophet(model, config["forecast_periods"], config.get("frequency", "D"))
    save_csv(forecast, config["paths"]["forecast_output"])
    logger.info("Demand forecast generated: rows=%s output=%s", len(forecast), config["paths"]["forecast_output"])
    return forecast


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/prophet_config.yaml")
    args = parser.parse_args()
    forecast_demand(args.config)
    print("Forecast generated")
