from __future__ import annotations
import argparse
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv, save_csv
from src.data.data_validator import validate_inventory_schema
from src.features.feature_pipeline import create_features
from src.models.xgboost_model import build_xgboost_classifier
from src.preprocessing.preprocessing_pipeline import build_preprocessing_pipeline, infer_feature_columns
from src.training.evaluate import (
    evaluate_binary_classifier, save_classification_report,
    save_confusion_matrix_plot, save_feature_importance_plot
)
from src.utils.metrics import find_best_threshold, save_json
from src.utils.save_load_model import save_object
from src.utils.config import load_yaml_config
from src.utils.error_handler import log_and_raise
from src.utils.exceptions import ModelTrainingError
from src.utils.logger import get_logger, log_exception

logger = get_logger(__name__)


@log_and_raise("XGBoost training failed", ModelTrainingError)
def train_xgboost(config_path: str = "configs/xgboost_config.yaml") -> dict:
    config = load_yaml_config(config_path, required_keys=["target_column", "date_column", "paths", "model"])
    target = config["target_column"]
    date_col = config["date_column"]
    id_cols = config.get("id_columns", [])
    paths = config["paths"]

    logger.info("Starting XGBoost training using config=%s", config_path)
    df = load_csv(paths["raw_data"])
    validate_inventory_schema(df, require_target=True)
    df = clean_inventory_data(df, require_target=True)
    featured = create_features(df)
    save_csv(featured, paths["processed_data"])

    drop_cols = [target, date_col, *id_cols]
    X = featured.drop(columns=drop_cols, errors="ignore")
    y = featured[target].astype(int)
    numeric_cols, categorical_cols = infer_feature_columns(featured, drop_cols)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config.get("test_size", 0.2),
        random_state=config.get("random_state", 42),
        stratify=y,
    )
    negative = int((y_train == 0).sum())
    positive = int((y_train == 1).sum())
    scale_pos_weight = negative / max(positive, 1)

    preprocessor = build_preprocessing_pipeline(numeric_cols, categorical_cols)
    model = build_xgboost_classifier(config["model"], scale_pos_weight=scale_pos_weight)
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    logger.info("Training XGBoost model with %s rows and %s features", len(X_train), X_train.shape[1])
    pipeline.fit(X_train, y_train)

    y_prob = pipeline.predict_proba(X_test)[:, 1]
    threshold_cfg = config.get("threshold", {})
    best_threshold, threshold_scores = find_best_threshold(
        y_test,
        y_prob,
        metric=threshold_cfg.get("optimize_for", "f1"),
        start=threshold_cfg.get("min_threshold", 0.1),
        stop=threshold_cfg.get("max_threshold", 0.9),
        step=threshold_cfg.get("step", 0.01),
    )
    metrics = evaluate_binary_classifier(y_test, y_prob, best_threshold)
    metrics.update({
        "rows": int(len(featured)),
        "original_columns": int(df.shape[1]),
        "engineered_columns": int(featured.shape[1]),
        "model_features": int(X.shape[1]),
        "target_positive_rate": float(y.mean()),
        "scale_pos_weight": float(scale_pos_weight),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
    })

    feature_list = X.columns.tolist()
    threshold_config = {
        "threshold": float(best_threshold),
        "optimized_for": threshold_cfg.get("optimize_for", "f1"),
        "min_threshold": threshold_cfg.get("min_threshold", 0.1),
        "max_threshold": threshold_cfg.get("max_threshold", 0.9),
        "step": threshold_cfg.get("step", 0.01),
    }
    model_metadata = {
        "model_name": "xgboost_stockout_classifier",
        "target_column": target,
        "date_column": date_col,
        "id_columns": id_cols,
        "raw_data_path": paths["raw_data"],
        "processed_data_path": paths["processed_data"],
        "rows": int(len(featured)),
        "original_columns": int(df.shape[1]),
        "engineered_columns": int(featured.shape[1]),
        "model_features": int(X.shape[1]),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "feature_list_path": paths.get("feature_list", "artifacts/feature_list.json"),
        "threshold_config_path": paths.get("threshold_config", "artifacts/threshold_config.json"),
    }

    save_object(pipeline, paths["model"])
    save_object(pipeline.named_steps["preprocessor"], paths["preprocessing_pipeline"])
    save_json(metrics, paths["metrics"])
    save_json({"features": feature_list}, paths.get("feature_list", "artifacts/feature_list.json"))
    save_json(model_metadata, paths.get("model_metadata", "artifacts/model_metadata.json"))
    save_json(threshold_config, paths.get("threshold_config", "artifacts/threshold_config.json"))
    save_classification_report(y_test, y_prob, best_threshold, paths["classification_report"])
    save_confusion_matrix_plot(y_test, y_prob, best_threshold, paths["confusion_matrix"])
    try:
        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
        save_feature_importance_plot(pipeline.named_steps["model"], feature_names, paths["feature_importance"])
    except Exception as exc:
        log_exception(logger, "Could not save feature importance plot", exc)

    threshold_scores.to_csv(Path(paths["metrics"]).with_name("threshold_scores.csv"), index=False)
    logger.info("Training completed. Metrics saved to %s", paths["metrics"])
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/xgboost_config.yaml")
    args = parser.parse_args()
    try:
        print(train_xgboost(args.config))
    except Exception as exc:
        logger.error("Training command failed: %s", exc)
        raise
