from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.data_cleaner import clean_inventory_data
from src.data.data_loader import load_csv
from src.features.feature_pipeline import create_features
from src.utils.metrics import save_json


def _numeric_psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    expected = pd.to_numeric(expected, errors="coerce").dropna()
    actual = pd.to_numeric(actual, errors="coerce").dropna()
    if expected.empty or actual.empty or expected.nunique() <= 1:
        return 0.0

    quantiles = np.linspace(0, 1, buckets + 1)
    edges = np.unique(np.quantile(expected, quantiles))
    if len(edges) < 3:
        return 0.0

    edges[0] = -np.inf
    edges[-1] = np.inf
    expected_counts = pd.cut(expected, bins=edges, include_lowest=True).value_counts(sort=False)
    actual_counts = pd.cut(actual, bins=edges, include_lowest=True).value_counts(sort=False)

    expected_pct = (expected_counts / max(expected_counts.sum(), 1)).replace(0, 1e-6)
    actual_pct = (actual_counts / max(actual_counts.sum(), 1)).replace(0, 1e-6)
    return float(((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)).sum())


def _categorical_shift(expected: pd.Series, actual: pd.Series) -> float:
    expected_pct = expected.astype("string").fillna("__missing__").value_counts(normalize=True)
    actual_pct = actual.astype("string").fillna("__missing__").value_counts(normalize=True)
    categories = expected_pct.index.union(actual_pct.index)
    return float((expected_pct.reindex(categories, fill_value=0) - actual_pct.reindex(categories, fill_value=0)).abs().max())


def generate_data_drift_report(
    baseline_path: str = "data/processed/processed_inventory.csv",
    current_path: str = "data/raw/healthcare_supply_chain_01.csv",
    output_path: str = "artifacts/data_drift_report.json",
) -> dict:
    baseline = load_csv(baseline_path) if Path(baseline_path).exists() else create_features(clean_inventory_data(load_csv(current_path), require_target=False))
    current = create_features(clean_inventory_data(load_csv(current_path), require_target=False))

    common_columns = [c for c in baseline.columns if c in current.columns]
    numeric_columns = [c for c in common_columns if pd.api.types.is_numeric_dtype(baseline[c])]
    categorical_columns = [c for c in common_columns if c not in numeric_columns]

    numeric_drift = {col: _numeric_psi(baseline[col], current[col]) for col in numeric_columns}
    categorical_drift = {col: _categorical_shift(baseline[col], current[col]) for col in categorical_columns}

    high_numeric = {k: v for k, v in numeric_drift.items() if v >= 0.25}
    high_categorical = {k: v for k, v in categorical_drift.items() if v >= 0.20}

    report = {
        "baseline_rows": int(len(baseline)),
        "current_rows": int(len(current)),
        "numeric_columns_checked": len(numeric_columns),
        "categorical_columns_checked": len(categorical_columns),
        "numeric_psi": numeric_drift,
        "categorical_max_share_shift": categorical_drift,
        "high_numeric_drift": high_numeric,
        "high_categorical_drift": high_categorical,
        "drift_detected": bool(high_numeric or high_categorical),
    }
    save_json(report, output_path)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="data/processed/processed_inventory.csv")
    parser.add_argument("--current", default="data/raw/healthcare_supply_chain_01.csv")
    parser.add_argument("--output", default="artifacts/data_drift_report.json")
    args = parser.parse_args()
    print(generate_data_drift_report(args.baseline, args.current, args.output))
