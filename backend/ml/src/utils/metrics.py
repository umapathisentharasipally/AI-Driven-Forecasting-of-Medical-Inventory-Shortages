from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
)


def classification_metrics(y_true: Iterable[int], y_pred: Iterable[int], y_prob: Iterable[float]) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
    }


def find_best_threshold(y_true: Iterable[int], y_prob: Iterable[float], metric: str = "f1", start: float = 0.1, stop: float = 0.9, step: float = 0.01) -> tuple[float, pd.DataFrame]:
    rows = []
    for threshold in np.arange(start, stop + step, step):
        y_pred = (np.asarray(y_prob) >= threshold).astype(int)
        rows.append({"threshold": float(threshold), **classification_metrics(y_true, y_pred, y_prob)})
    scores = pd.DataFrame(rows)
    if metric not in scores.columns:
        raise ValueError(f"Unsupported threshold metric: {metric}")
    best = scores.sort_values(metric, ascending=False).iloc[0]
    return float(best["threshold"]), scores


def save_json(data: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def confusion_matrix_dict(y_true: Iterable[int], y_pred: Iterable[int]) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
