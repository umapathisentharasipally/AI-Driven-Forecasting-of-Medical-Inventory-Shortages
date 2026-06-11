from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd
import yaml
from src.features.feature_pipeline import create_features
from src.models.risk_engine import apply_risk_engine
from src.utils.save_load_model import load_object

class RealtimeStockoutPredictor:
    def __init__(self, config_path: str = "configs/xgboost_config.yaml", risk_config_path: str = "configs/risk_engine_config.yaml"):
        base_dir = Path(__file__).resolve().parents[2]

        self.config_path = Path(config_path)
        if not self.config_path.is_absolute():
            self.config_path = (base_dir / self.config_path).resolve()

        self.risk_config_path = Path(risk_config_path)
        if not self.risk_config_path.is_absolute():
            self.risk_config_path = (base_dir / self.risk_config_path).resolve()

        with self.config_path.open("r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)
        with self.risk_config_path.open("r", encoding="utf-8") as file:
            self.risk_config = yaml.safe_load(file)

        model_path = Path(self.config["paths"]["model"])
        if not model_path.is_absolute():
            model_path = (base_dir / model_path).resolve()

        self.pipeline = load_object(model_path)

        metrics_path = Path(self.config["paths"]["metrics"])
        if not metrics_path.is_absolute():
            metrics_path = (base_dir / metrics_path).resolve()

        self.threshold = 0.5
        if metrics_path.exists():
            self.threshold = json.loads(metrics_path.read_text(encoding="utf-8")).get("threshold", 0.5)

    def predict_one(self, record: dict[str, Any]) -> dict[str, Any]:
        df = pd.DataFrame([record])
        featured = create_features(df)
        drop_cols = [self.config["target_column"], self.config["date_column"], *self.config.get("id_columns", [])]
        X = featured.drop(columns=drop_cols, errors="ignore")
        probability = float(self.pipeline.predict_proba(X)[:, 1][0])
        output = df.copy()
        output["stockout_probability"] = probability
        output["stockout_prediction"] = int(probability >= self.threshold)
        output = apply_risk_engine(output, self.risk_config)
        return output.iloc[0].to_dict()
