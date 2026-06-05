from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.features.feature_pipeline import create_features
from src.models.risk_engine import apply_risk_engine
from src.utils.config import load_yaml_config
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelInferenceError
from src.utils.logger import get_logger, log_exception
from src.utils.save_load_model import load_object

logger = get_logger(__name__)


def _load_threshold(config: dict) -> float:
    threshold_path = Path(config["paths"].get("threshold_config", "artifacts/threshold_config.json"))
    metrics_path = Path(config["paths"]["metrics"])
    try:
        if threshold_path.exists():
            return float(json.loads(threshold_path.read_text(encoding="utf-8")).get("threshold", 0.5))
        if metrics_path.exists():
            return float(json.loads(metrics_path.read_text(encoding="utf-8")).get("threshold", 0.5))
        logger.warning("Threshold file not found. Using default threshold=0.5")
        return 0.5
    except Exception as exc:
        log_exception(logger, "Could not load threshold. Using default threshold=0.5", exc)
        return 0.5


def _align_features(featured, config: dict):
    drop_cols = [config["target_column"], config["date_column"], *config.get("id_columns", [])]
    X = featured.drop(columns=drop_cols, errors="ignore")
    feature_list_path = Path(config["paths"].get("feature_list", "artifacts/feature_list.json"))
    if not feature_list_path.exists():
        logger.warning("Feature list file not found. Using generated feature columns directly: %s", feature_list_path)
        return X
    features = json.loads(feature_list_path.read_text(encoding="utf-8")).get("features", [])
    if not features:
        raise ModelInferenceError(f"Feature list is empty: {feature_list_path}")
    for col in features:
        if col not in X.columns:
            X[col] = None
    extra_cols = sorted(set(X.columns) - set(features))
    if extra_cols:
        logger.info("Dropping %s extra inference columns not seen during training", len(extra_cols))
    return X[features]


@log_and_raise("Stockout prediction failed", ModelInferenceError)
def predict_stockout(
    input_path: str,
    output_path: str = "data/predictions/prediction_results.csv",
    config_path: str = "configs/xgboost_config.yaml",
    risk_config_path: str = "configs/risk_engine_config.yaml",
):
    config = load_yaml_config(config_path, required_keys=["target_column", "date_column", "paths"])
    risk_config = load_yaml_config(risk_config_path)
    pipeline = load_object(config["paths"]["model"])
    threshold = _load_threshold(config)

    df = clean_inventory_data(load_csv(input_path), require_target=False)
    featured = create_features(df)
    X = _align_features(featured, config)

    logger.info("Running stockout prediction: rows=%s features=%s threshold=%.4f", X.shape[0], X.shape[1], threshold)
    probabilities = pipeline.predict_proba(X)[:, 1]

    output = df.copy()
    output["stockout_probability"] = probabilities
    output["stockout_prediction"] = (probabilities >= threshold).astype(int)
    output = apply_risk_engine(output, risk_config)
    save_csv(output, output_path)
    logger.info("Predictions saved: %s", output_path)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/healthcare_supply_chain_01.csv")
    parser.add_argument("--output", default="data/predictions/prediction_results.csv")
    parser.add_argument("--config", default="configs/xgboost_config.yaml")
    args = parser.parse_args()
    predict_stockout(args.input, args.output, args.config)
    print(f"Predictions saved to {args.output}")
