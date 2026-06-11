from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, classification_report
from src.utils.metrics import classification_metrics, confusion_matrix_dict, save_json


def evaluate_binary_classifier(y_true, y_prob, threshold: float) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    metrics = classification_metrics(y_true, y_pred, y_prob)
    metrics["threshold"] = float(threshold)
    metrics["confusion_matrix"] = confusion_matrix_dict(y_true, y_pred)
    return metrics


def save_classification_report(y_true, y_prob, threshold: float, path: str | Path) -> None:
    y_pred = (y_prob >= threshold).astype(int)
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    save_json(report, path)


def save_confusion_matrix_plot(y_true, y_prob, threshold: float, path: str | Path) -> None:
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        y_pred = (y_prob >= threshold).astype(int)
        ConfusionMatrixDisplay.from_predictions(y_true, y_pred, values_format="d")
        plt.title("XGBoost Stockout Confusion Matrix")
        plt.tight_layout()
        plt.savefig(path, dpi=140)
        plt.close()
    except Exception:
        plt.close()
        return


def save_feature_importance_plot(model, feature_names: list[str], path: str | Path, top_n: int = 25) -> None:
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            return
        frame = pd.DataFrame({"feature": feature_names[:len(importances)], "importance": importances})
        frame = frame.sort_values("importance", ascending=False).head(top_n)
        plt.figure(figsize=(10, 7))
        plt.barh(frame["feature"][::-1], frame["importance"][::-1])
        plt.title("Top XGBoost Feature Importance")
        plt.xlabel("Importance")
        plt.tight_layout()
        plt.savefig(path, dpi=140)
        plt.close()
    except Exception:
        plt.close()
        return
