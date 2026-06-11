from __future__ import annotations

import argparse

from src.training.train_anomaly_model import train_anomaly_model
from src.inference.detect_anomalies import detect_anomalies
from src.utils.metrics import save_json


def run_anomaly_pipeline(
    input_path: str = "data/raw/healthcare_supply_chain_01.csv",
    config_path: str = "configs/anomaly_config.yaml",
) -> dict:
    training_report = train_anomaly_model(config_path)
    anomaly_output = detect_anomalies(input_path, config_path)
    report = {
        "training": training_report,
        "inference_rows": int(len(anomaly_output)),
        "inference_anomalies": int(anomaly_output["is_anomaly"].sum()),
        "inference_anomaly_rate": float(anomaly_output["is_anomaly"].mean()),
    }
    save_json(report, "artifacts/anomaly_pipeline_report.json")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/healthcare_supply_chain_01.csv")
    parser.add_argument("--config", default="configs/anomaly_config.yaml")
    args = parser.parse_args()
    print(run_anomaly_pipeline(args.input, args.config))
