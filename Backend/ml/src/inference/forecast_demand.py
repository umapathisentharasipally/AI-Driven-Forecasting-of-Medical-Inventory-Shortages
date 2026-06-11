from __future__ import annotations
import argparse
import yaml
from src.models.prophet_model import forecast_with_prophet
from src.data.data_loader import save_csv
from src.utils.save_load_model import load_object


def forecast_demand(config_path: str = "configs/prophet_config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    model = load_object(config["paths"]["model"])
    forecast = forecast_with_prophet(model, config["forecast_periods"], config.get("frequency", "D"))
    save_csv(forecast, config["paths"]["forecast_output"])
    return forecast


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/prophet_config.yaml")
    args = parser.parse_args()
    forecast_demand(args.config)
    print("Forecast generated")
