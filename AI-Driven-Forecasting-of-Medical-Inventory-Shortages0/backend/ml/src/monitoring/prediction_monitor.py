from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.utils.metrics import save_json


def generate_prediction_report(
    prediction_path: str = "data/predictions/prediction_results.csv",
    output_path: str = "artifacts/prediction_monitor_report.json",
) -> dict:
    path = Path(prediction_path)
    if not path.exists():
        raise FileNotFoundError(f"Prediction file not found: {prediction_path}")

    df = pd.read_csv(path)
    if "stockout_probability" not in df.columns or "stockout_prediction" not in df.columns:
        raise ValueError("Prediction file must contain stockout_probability and stockout_prediction columns")

    probability = pd.to_numeric(df["stockout_probability"], errors="coerce")
    report = {
        "rows": int(len(df)),
        "predicted_stockouts": int(pd.to_numeric(df["stockout_prediction"], errors="coerce").fillna(0).sum()),
        "predicted_stockout_rate": float(pd.to_numeric(df["stockout_prediction"], errors="coerce").fillna(0).mean()),
        "probability_mean": float(probability.mean()),
        "probability_p50": float(probability.quantile(0.50)),
        "probability_p90": float(probability.quantile(0.90)),
        "probability_p95": float(probability.quantile(0.95)),
        "probability_p99": float(probability.quantile(0.99)),
    }
    if "risk_level" in df.columns:
        report["risk_level_counts"] = df["risk_level"].astype("string").value_counts(dropna=False).to_dict()

    save_json(report, output_path)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default="data/predictions/prediction_results.csv")
    parser.add_argument("--output", default="artifacts/prediction_monitor_report.json")
    args = parser.parse_args()
    print(generate_prediction_report(args.predictions, args.output))
