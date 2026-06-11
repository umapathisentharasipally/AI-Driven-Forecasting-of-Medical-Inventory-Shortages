from __future__ import annotations
import argparse
import json
import yaml
import pandas as pd
from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.features.anomaly_features import build_anomaly_features
from src.models.isolation_forest_model import build_isolation_forest
from src.preprocessing.preprocessing_pipeline import build_preprocessing_pipeline
from src.utils.save_load_model import save_object
from src.utils.logger import get_logger

logger = get_logger(__name__)


def train_anomaly_model(config_path: str = "configs/anomaly_config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    paths = config["paths"]
    df = clean_inventory_data(load_csv(paths["raw_data"]), require_target=False)
    data = build_anomaly_features(df)
    feature_cols = [c for c in config["feature_columns"] if c in data.columns]
    extra_cols = ["usage_ratio_30_90", "stock_to_safety_ratio", "lead_time_ratio"]
    feature_cols.extend([c for c in extra_cols if c in data.columns])
    X = data[feature_cols].copy()
    preprocessor = build_preprocessing_pipeline(feature_cols, [])
    X_processed = preprocessor.fit_transform(X)
    model = build_isolation_forest(config.get("contamination", 0.03), config.get("random_state", 42))
    predictions = model.fit_predict(X_processed)
    scores = -model.score_samples(X_processed)
    output = data[config.get("id_columns", []) + [config.get("date_column", "snapshot_date")]].copy()
    output["anomaly_score"] = scores
    output["is_anomaly"] = (predictions == -1).astype(int)
    save_csv(output, paths["anomaly_output"])
    save_object({"model": model, "preprocessor": preprocessor, "feature_columns": feature_cols}, paths["model"])
    report = {"rows": int(len(output)), "anomalies": int(output["is_anomaly"].sum()), "anomaly_rate": float(output["is_anomaly"].mean())}
    with open(paths["report"], "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    logger.info("Anomaly model saved to %s", paths["model"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/anomaly_config.yaml")
    args = parser.parse_args()
    print(train_anomaly_model(args.config))
