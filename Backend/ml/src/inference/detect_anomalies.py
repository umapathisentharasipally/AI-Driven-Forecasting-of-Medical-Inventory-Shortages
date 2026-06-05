from __future__ import annotations

import argparse

from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.features.anomaly_features import build_anomaly_features
from src.utils.config import load_yaml_config
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelInferenceError
from src.utils.logger import get_logger
from src.utils.save_load_model import load_object

logger = get_logger(__name__)


@log_and_raise("Anomaly inference failed", ModelInferenceError)
def detect_anomalies(input_path: str = "data/raw/healthcare_supply_chain_01.csv", config_path: str = "configs/anomaly_config.yaml"):
    config = load_yaml_config(config_path, required_keys=["paths"])
    artifact = load_object(config["paths"]["model"])
    required_keys = {"model", "preprocessor", "feature_columns"}
    missing = required_keys - set(artifact.keys())
    if missing:
        raise ModelInferenceError(f"Invalid anomaly artifact. Missing keys: {sorted(missing)}")

    df = clean_inventory_data(load_csv(input_path), require_target=False)
    data = build_anomaly_features(df)
    missing_features = [col for col in artifact["feature_columns"] if col not in data.columns]
    if missing_features:
        raise ModelInferenceError(f"Missing anomaly features in input data: {missing_features}")

    X = data[artifact["feature_columns"]]
    X_processed = artifact["preprocessor"].transform(X)
    predictions = artifact["model"].predict(X_processed)
    scores = -artifact["model"].score_samples(X_processed)

    output = df.copy()
    output["anomaly_score"] = scores
    output["is_anomaly"] = (predictions == -1).astype(int)
    save_csv(output, config["paths"]["anomaly_output"])
    logger.info("Anomaly inference completed: rows=%s anomalies=%s", len(output), int(output["is_anomaly"].sum()))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/healthcare_supply_chain_01.csv")
    parser.add_argument("--config", default="configs/anomaly_config.yaml")
    args = parser.parse_args()
    detect_anomalies(args.input, args.config)
    print("Anomaly results generated")
