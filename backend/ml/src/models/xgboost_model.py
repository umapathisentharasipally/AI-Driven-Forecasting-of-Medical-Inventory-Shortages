from __future__ import annotations
from xgboost import XGBClassifier


def build_xgboost_classifier(params: dict, scale_pos_weight: float | None = None) -> XGBClassifier:
    model_params = dict(params)
    if scale_pos_weight is not None:
        model_params["scale_pos_weight"] = scale_pos_weight
    return XGBClassifier(**model_params)
