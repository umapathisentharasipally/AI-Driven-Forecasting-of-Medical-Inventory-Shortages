from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.utils.error_handler import log_and_raise
from src.utils.exceptions import MonitoringError
from src.utils.logger import get_logger
from src.utils.metrics import save_json

logger = get_logger(__name__)


@log_and_raise("Prediction monitoring failed", MonitoringError)
def generate_prediction_report(
    prediction_path: str = "data/predictions/prediction_results.csv",
    output_path: str = "artifacts/prediction_monitor_report.json",
) -> dict:
    path = Path(prediction_path)
    if not path.exists():
        raise MonitoringError(f"Prediction file not found: {prediction_path}")

    df = pd.read_csv(path)
    required = {"stockout_probability", "stockout_prediction"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise MonitoringError(f"Prediction file missing required columns: {missing}")

    probability = pd.to_numeric(df["stockout_probability"], errors="coerce")
    if probability.isna().all():
        raise MonitoringError("stockout_probability column contains no valid numeric values")

    prediction = pd.to_numeric(df["stockout_prediction"], errors="coerce").fillna(0)
    report = {
        "rows": int(len(df)),
        "predicted_stockouts": int(prediction.sum()),
        "predicted_stockout_rate": float(prediction.mean()),
        "probability_mean": float(probability.mean()),
        "probability_p50": float(probability.quantile(0.50)),
        "probability_p90": float(probability.quantile(0.90)),
        "probability_p95": float(probability.quantile(0.95)),
        "probability_p99": float(probability.quantile(0.99)),
    }
    if "risk_level" in df.columns:
        report["risk_level_counts"] = df["risk_level"].astype("string").value_counts(dropna=False).to_dict()

    save_json(report, output_path)
    logger.info("Prediction monitoring report saved: %s", output_path)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default="data/predictions/prediction_results.csv")
    parser.add_argument("--output", default="artifacts/prediction_monitor_report.json")
    args = parser.parse_args()
    print(generate_prediction_report(args.predictions, args.output))
