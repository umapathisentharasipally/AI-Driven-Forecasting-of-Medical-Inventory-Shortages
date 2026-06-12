from __future__ import annotations
import argparse
import json
import yaml
from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.models.prophet_model import build_prophet_model, forecast_with_prophet, prepare_prophet_frame
from src.utils.save_load_model import save_object
from src.utils.logger import get_logger

logger = get_logger(__name__)


def train_prophet(config_path: str = "configs/prophet_config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    paths = config["paths"]
    df = clean_inventory_data(load_csv(paths["raw_data"]), require_target=False)
    prophet_df = prepare_prophet_frame(df, config["date_column"], config["target_column"])
    if len(prophet_df) < 30:
        raise ValueError("Prophet needs at least 30 daily observations for a useful forecast")
    model = build_prophet_model(config["model"])
    model.fit(prophet_df)
    forecast = forecast_with_prophet(model, periods=config["forecast_periods"], freq=config.get("frequency", "D"))
    save_csv(forecast, paths["forecast_output"])
    save_object(model, paths["model"])
    report = {
        "training_days": int(len(prophet_df)),
        "forecast_rows": int(len(forecast)),
        "target_column": config["target_column"],
        "last_training_date": str(prophet_df["ds"].max()),
        "last_forecast_date": str(forecast["ds"].max()),
    }
    with open(paths["trend_report"], "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    logger.info("Prophet forecast saved to %s", paths["forecast_output"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/prophet_config.yaml")
    args = parser.parse_args()
    print(train_prophet(args.config))
