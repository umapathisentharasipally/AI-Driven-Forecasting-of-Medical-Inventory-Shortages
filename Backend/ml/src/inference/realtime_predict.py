from __future__ import annotations

from typing import Any

import pandas as pd

from src.features.feature_pipeline import create_features
from src.inference.predict_stockout import _align_features, _load_threshold
from src.models.risk_engine import apply_risk_engine
from src.utils.config import load_yaml_config
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelInferenceError
from src.utils.logger import get_logger
from src.utils.save_load_model import load_object

logger = get_logger(__name__)


class RealtimeStockoutPredictor:
    """Reusable predictor for API/Kafka real-time stockout scoring."""

    def __init__(self, config_path: str = "configs/xgboost_config.yaml", risk_config_path: str = "configs/risk_engine_config.yaml"):
        self.config = load_yaml_config(config_path, required_keys=["target_column", "date_column", "paths"])
        self.risk_config = load_yaml_config(risk_config_path)
        self.pipeline = load_object(self.config["paths"]["model"])
        self.threshold = _load_threshold(self.config)
        logger.info("RealtimeStockoutPredictor initialized with threshold=%.4f", self.threshold)

    @log_and_raise("Realtime prediction failed", ModelInferenceError)
    def predict_one(self, record: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(record, dict) or not record:
            raise ModelInferenceError("Realtime prediction input must be a non-empty dictionary")
        df = pd.DataFrame([record])
        featured = create_features(df)
        X = _align_features(featured, self.config)
        probability = float(self.pipeline.predict_proba(X)[:, 1][0])
        output = df.copy()
        output["stockout_probability"] = probability
        output["stockout_prediction"] = int(probability >= self.threshold)
        output = apply_risk_engine(output, self.risk_config)
        return output.iloc[0].to_dict()
