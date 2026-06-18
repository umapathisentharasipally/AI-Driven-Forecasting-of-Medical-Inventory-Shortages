from __future__ import annotations
import argparse
import json
import yaml
from pathlib import Path
from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.features.feature_pipeline import create_features
from src.models.risk_engine import apply_risk_engine
from src.utils.save_load_model import load_object


def predict_stockout(input_path: str, output_path: str = "data/predictions/prediction_results.csv", config_path: str = "configs/xgboost_config.yaml", risk_config_path: str = "configs/risk_engine_config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    with open(risk_config_path, "r", encoding="utf-8") as file:
        risk_config = yaml.safe_load(file)
    pipeline = load_object(config["paths"]["model"])
    metrics_path = Path(config["paths"]["metrics"])
    threshold = 0.5
    if metrics_path.exists():
        threshold = json.loads(metrics_path.read_text(encoding="utf-8")).get("threshold", 0.5)
    df = clean_inventory_data(load_csv(input_path), require_target=False)
    featured = create_features(df)
    drop_cols = [config["target_column"], config["date_column"], *config.get("id_columns", [])]
    X = featured.drop(columns=drop_cols, errors="ignore")
    probabilities = pipeline.predict_proba(X)[:, 1]
    output = df.copy()
    output["stockout_probability"] = probabilities
    output["stockout_prediction"] = (probabilities >= threshold).astype(int)
    output = apply_risk_engine(output, risk_config)
    save_csv(output, output_path)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/medical_inventory.csv")
    parser.add_argument("--output", default="data/predictions/prediction_results.csv")
    parser.add_argument("--config", default="configs/xgboost_config.yaml")
    args = parser.parse_args()
    predict_stockout(args.input, args.output, args.config)
    print(f"Predictions saved to {args.output}")
