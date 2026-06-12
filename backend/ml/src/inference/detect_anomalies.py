from __future__ import annotations
import argparse
import yaml
from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.features.anomaly_features import build_anomaly_features
from src.utils.save_load_model import load_object


def detect_anomalies(input_path: str = "data/raw/medical_inventory.csv", config_path: str = "configs/anomaly_config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    artifact = load_object(config["paths"]["model"])
    df = clean_inventory_data(load_csv(input_path), require_target=False)
    data = build_anomaly_features(df)
    X = data[artifact["feature_columns"]]
    X_processed = artifact["preprocessor"].transform(X)
    predictions = artifact["model"].predict(X_processed)
    scores = -artifact["model"].score_samples(X_processed)
    output = df.copy()
    output["anomaly_score"] = scores
    output["is_anomaly"] = (predictions == -1).astype(int)
    save_csv(output, config["paths"]["anomaly_output"])
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/medical_inventory.csv")
    parser.add_argument("--config", default="configs/anomaly_config.yaml")
    args = parser.parse_args()
    detect_anomalies(args.input, args.config)
    print("Anomaly results generated")
