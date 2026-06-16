from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv
from src.features.feature_pipeline import create_features
from src.training.evaluate import evaluate_binary_classifier
from src.utils.metrics import save_json
from src.utils.save_load_model import load_object


def evaluate_model_on_labeled_data(
    input_path: str = "data/raw/healthcare_supply_chain_01.csv",
    config_path: str = "configs/xgboost_config.yaml",
    output_path: str = "artifacts/model_drift_report.json",
) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    target = config["target_column"]
    paths = config["paths"]
    threshold_path = Path(paths.get("threshold_config", "artifacts/threshold_config.json"))
    threshold = 0.5
    if threshold_path.exists():
        threshold = json.loads(threshold_path.read_text(encoding="utf-8")).get("threshold", 0.5)

    df = clean_inventory_data(load_csv(input_path), require_target=True)
    featured = create_features(df)
    drop_cols = [target, config["date_column"], *config.get("id_columns", [])]
    X = featured.drop(columns=drop_cols, errors="ignore")
    y = featured[target].astype(int)

    pipeline = load_object(paths["model"])
    y_prob = pipeline.predict_proba(X)[:, 1]
    current_metrics = evaluate_binary_classifier(y, y_prob, threshold)

    training_metrics = {}
    metrics_path = Path(paths["metrics"])
    if metrics_path.exists():
        training_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    metric_drop = {}
    for metric in ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]:
        if metric in training_metrics and metric in current_metrics:
            metric_drop[metric] = float(training_metrics[metric] - current_metrics[metric])

    report = {
        "rows_evaluated": int(len(df)),
        "threshold": float(threshold),
        "current_metrics": current_metrics,
        "training_metrics": training_metrics,
        "metric_drop": metric_drop,
        "model_drift_detected": any(drop >= 0.10 for drop in metric_drop.values()),
    }
    save_json(report, output_path)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/healthcare_supply_chain_01.csv")
    parser.add_argument("--config", default="configs/xgboost_config.yaml")
    parser.add_argument("--output", default="artifacts/model_drift_report.json")
    args = parser.parse_args()
    print(evaluate_model_on_labeled_data(args.input, args.config, args.output))
