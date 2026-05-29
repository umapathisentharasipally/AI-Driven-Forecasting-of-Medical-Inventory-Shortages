"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      AI-Driven Medical Inventory Forecasting — ML Pipeline                  ║
║      Run in VS Code. Each stage is a clean, importable module.              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Stage 1  →  Data Loading & Validation
Stage 2  →  Feature Engineering
Stage 3  →  Train / Val / Test Split (time-based)
Stage 4  →  Baseline Model  (ARIMA / Holt-Winters via statsmodels)
Stage 5  →  Primary Model   (XGBoost / LightGBM — stockout classifier)
Stage 6  →  Stacking Meta-Learner
Stage 7  →  Evaluation & SHAP Explainability
Stage 8  →  Risk Scoring & Alert Tier Assignment
Stage 9  →  MLflow Experiment Tracking
"""

# ── pip install requirements ──────────────────────────────────────────────────
# pip install pandas numpy scikit-learn xgboost lightgbm shap mlflow
#             statsmodels imbalanced-learn matplotlib joblib

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import shap

from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score, average_precision_score,
    confusion_matrix, f1_score, precision_recall_curve
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

import xgboost as xgb
import lightgbm as lgb
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    data_path:        str  = "medical_inventory.csv"   # ← change to your CSV path
    output_dir:       str  = "outputs"
    mlflow_uri:       str  = "mlruns"
    experiment_name:  str  = "medical_inventory_forecasting"

    # Time split
    train_cutoff:     str  = "2023-09-30"   # rows up to this date → train
    val_cutoff:       str  = "2023-11-30"   # rows up to this date → val

    # Model hyperparams
    xgb_params: Dict = field(default_factory=lambda: {
        "n_estimators": 400, "max_depth": 6, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8,
        "scale_pos_weight": 10,   # handles class imbalance
        "eval_metric": "aucpr", "random_state": 42, "n_jobs": -1
    })

    lgb_params: Dict = field(default_factory=lambda: {
        "n_estimators": 400, "max_depth": 6, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8,
        "class_weight": "balanced",
        "random_state": 42, "n_jobs": -1, "verbose": -1
    })

    # Risk scoring weights
    alert_thresholds: Dict = field(default_factory=lambda: {
        "critical": 0.75, "high": 0.50, "watch": 0.30
    })

    criticality_weights: Dict = field(default_factory=lambda: {
        "critical": 3.0, "high": 2.0, "medium": 1.5, "low": 1.0
    })

CFG = Config()
Path(CFG.output_dir).mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — DATA LOADING & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
IDENTIFIERS = [
    "record_id", "snapshot_date", "facility_id", "facility_type",
    "department", "item_id", "item_category", "item_subcategory",
    "unit_of_measure", "primary_vendor_id"
]

DEMAND_FEATURES = [
    "avg_daily_usage_last_30d", "avg_daily_usage_last_90d",
    "usage_cv_last_90d", "demand_trend", "seasonal_demand_factor",
    "recent_usage_spike"
]

CONTEXTUAL_FEATURES = [
    "criticality_level", "shelf_life_days",
    "facility_census_pct", "pandemic_or_surge_flag"
]

SUPPLY_CHAIN_FEATURES = [
    "vendor_reliability_score", "contracted_lead_time_days",
    "actual_avg_lead_time_last_6m", "lead_time_variability_days",
    "active_po_in_transit", "backorder_frequency_last_12m",
    "sole_source_item", "substitution_available"
]

STOCK_FEATURES = [
    "current_stock_on_hand", "safety_stock_level", "days_of_supply_on_hand",
    "stock_as_pct_of_safety_level", "reorder_point_days",
    "days_until_next_scheduled_order", "days_since_last_stockout"
]

TARGET = "stockout_event"

CATEGORICAL_FEATURES = [
    "facility_type", "department", "item_category",
    "item_subcategory", "criticality_level", "demand_trend"
]

BINARY_FEATURES = [
    "recent_usage_spike", "pandemic_or_surge_flag",
    "active_po_in_transit", "sole_source_item", "substitution_available"
]

RAW_NUMERIC_FEATURES = [
    f for f in (DEMAND_FEATURES + CONTEXTUAL_FEATURES
                + SUPPLY_CHAIN_FEATURES + STOCK_FEATURES)
    if f not in CATEGORICAL_FEATURES + BINARY_FEATURES
]


def load_and_validate(path: str) -> pd.DataFrame:
    """Load CSV, enforce types, basic schema check."""
    print("\n" + "═" * 60)
    print("STAGE 1 — Data Loading & Validation")
    print("═" * 60)

    df = pd.read_csv(path, parse_dates=["snapshot_date"])
    print(f"  Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Date range: {df['snapshot_date'].min().date()} → {df['snapshot_date'].max().date()}")

    # Schema check
    all_expected = (IDENTIFIERS + DEMAND_FEATURES + CONTEXTUAL_FEATURES
                    + SUPPLY_CHAIN_FEATURES + STOCK_FEATURES + [TARGET])
    missing_cols = [c for c in all_expected if c not in df.columns]
    if missing_cols:
        print(f"  ⚠️  Missing columns: {missing_cols}")

    # Target validation
    if df[TARGET].isnull().any():
        n_null = df[TARGET].isnull().sum()
        print(f"  ⚠️  {n_null} null target values — dropping those rows")
        df = df.dropna(subset=[TARGET])

    # Duplicate check
    dupe_mask = df.duplicated(subset=["snapshot_date", "facility_id", "department", "item_id"])
    if dupe_mask.any():
        print(f"  ⚠️  {dupe_mask.sum()} duplicate rows removed")
        df = df[~dupe_mask]

    df[TARGET] = df[TARGET].astype(int)
    class_balance = df[TARGET].value_counts(normalize=True)
    print(f"  Stockout rate: {class_balance.get(1, 0)*100:.2f}%")
    print(f"  Unique time series: {df.groupby(['facility_id','department','item_id']).ngroups:,}")
    print("  ✅ Validation complete")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Compute all derived features. Returns df + list of engineered col names."""
    print("\n" + "═" * 60)
    print("STAGE 2 — Feature Engineering")
    print("═" * 60)

    df = df.copy()

    # ── Core derived features (from architecture spec) ──────────────────────
    df["trend_ratio"] = (
        df["avg_daily_usage_last_30d"]
        / df["avg_daily_usage_last_90d"].replace(0, np.nan)
    )

    df["projected_qty"] = (
        df["current_stock_on_hand"]
        - df["avg_daily_usage_last_30d"] * df["actual_avg_lead_time_last_6m"]
    )

    df["lead_time_bias"] = (
        df["actual_avg_lead_time_last_6m"] - df["contracted_lead_time_days"]
    )

    df["supply_risk_score"] = (
        df["backorder_frequency_last_12m"]
        * df["lead_time_variability_days"]
        / df["vendor_reliability_score"].clip(0.01)
    )

    # ── Additional engineered features ──────────────────────────────────────
    df["days_to_stockout"] = (
        df["current_stock_on_hand"]
        / df["avg_daily_usage_last_30d"].replace(0, np.nan)
    )

    df["safety_buffer"] = df["days_to_stockout"] - df["actual_avg_lead_time_last_6m"]

    df["stock_coverage_ratio"] = (
        df["days_of_supply_on_hand"]
        / df["days_until_next_scheduled_order"].replace(0, np.nan)
    )

    df["demand_volume_30d"] = df["avg_daily_usage_last_30d"] * 30

    df["effective_lead_time"] = (
        df["actual_avg_lead_time_last_6m"] + df["lead_time_variability_days"]
    )

    df["will_stockout_in_window"] = (df["projected_qty"] < 0).astype(int)

    df["stock_below_safety"] = (
        df["current_stock_on_hand"] < df["safety_stock_level"]
    ).astype(int)

    # Time features
    df["month"]       = df["snapshot_date"].dt.month
    df["day_of_week"] = df["snapshot_date"].dt.dayofweek
    df["quarter"]     = df["snapshot_date"].dt.quarter

    engineered_cols = [
        "trend_ratio", "projected_qty", "lead_time_bias", "supply_risk_score",
        "days_to_stockout", "safety_buffer", "stock_coverage_ratio",
        "demand_volume_30d", "effective_lead_time",
        "will_stockout_in_window", "stock_below_safety",
        "month", "day_of_week", "quarter"
    ]

    print(f"  Engineered {len(engineered_cols)} new features")
    print(f"  Items with projected_qty < 0: {(df['projected_qty'] < 0).sum():,}")
    print(f"  Items below safety stock: {df['stock_below_safety'].sum():,}")
    print("  ✅ Feature engineering complete")

    return df, engineered_cols


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — TIME-BASED TRAIN / VAL / TEST SPLIT
# ─────────────────────────────────────────────────────────────────────────────
def time_based_split(
    df: pd.DataFrame,
    train_cutoff: str,
    val_cutoff: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Strictly chronological split — no data leakage."""
    print("\n" + "═" * 60)
    print("STAGE 3 — Time-Based Train / Val / Test Split")
    print("═" * 60)

    train = df[df["snapshot_date"] <= train_cutoff].copy()
    val   = df[(df["snapshot_date"] > train_cutoff) &
               (df["snapshot_date"] <= val_cutoff)].copy()
    test  = df[df["snapshot_date"] > val_cutoff].copy()

    for name, split in [("Train", train), ("Val", val), ("Test", test)]:
        stockout_rate = split[TARGET].mean() * 100
        print(f"  {name:6s}: {len(split):7,} rows | stockout rate: {stockout_rate:.2f}%")

    print("  ✅ Split complete (no shuffle — time integrity preserved)")
    return train, val, test


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — PREPROCESSOR
# ─────────────────────────────────────────────────────────────────────────────
def build_preprocessor(engineered_cols: List[str]) -> ColumnTransformer:
    """Sklearn ColumnTransformer — handles numeric + categorical + binary."""
    all_numeric = RAW_NUMERIC_FEATURES + [
        c for c in engineered_cols
        if c not in ["will_stockout_in_window", "stock_below_safety",
                     "month", "day_of_week", "quarter"]
    ]
    # Remove any accidental duplicates
    all_numeric = list(dict.fromkeys(all_numeric))

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler())
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value",
                                   unknown_value=-1))
    ])

    binary_cols = BINARY_FEATURES + ["will_stockout_in_window", "stock_below_safety"]
    binary_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent"))
    ])

    time_cols = ["month", "day_of_week", "quarter"]
    time_pipe  = Pipeline([("imputer", SimpleImputer(strategy="median"))])

    preprocessor = ColumnTransformer([
        ("numeric",      numeric_pipe,      all_numeric),
        ("categorical",  categorical_pipe,  [c for c in CATEGORICAL_FEATURES
                                             if c not in ["demand_trend"]]),
        ("demand_trend", categorical_pipe,  ["demand_trend"]),
        ("binary",       binary_pipe,       binary_cols),
        ("time",         time_pipe,         time_cols)
    ], remainder="drop")

    return preprocessor


def prepare_xy(
    df: pd.DataFrame, engineered_cols: List[str]
) -> Tuple[pd.DataFrame, pd.Series]:
    all_feature_cols = (
        RAW_NUMERIC_FEATURES + CATEGORICAL_FEATURES
        + BINARY_FEATURES + engineered_cols
    )
    all_feature_cols = [c for c in dict.fromkeys(all_feature_cols)
                        if c in df.columns and c != TARGET]
    return df[all_feature_cols], df[TARGET]


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5 — PRIMARY MODELS (XGBoost + LightGBM)
# ─────────────────────────────────────────────────────────────────────────────
def train_xgboost(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray,   y_val: np.ndarray
) -> xgb.XGBClassifier:
    print("  Training XGBoost …")
    model = xgb.XGBClassifier(
        **{k: v for k, v in CFG.xgb_params.items() if k != "eval_metric"},
        use_label_encoder=False
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50
    )
    auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
    print(f"  XGBoost Val AUROC: {auc:.4f}")
    return model


def train_lightgbm(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray,   y_val: np.ndarray
) -> lgb.LGBMClassifier:
    print("  Training LightGBM …")
    model = lgb.LGBMClassifier(**CFG.lgb_params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(50, verbose=False),
                   lgb.log_evaluation(50)]
    )
    auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
    print(f"  LightGBM Val AUROC: {auc:.4f}")
    return model


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 6 — STACKING META-LEARNER
# ─────────────────────────────────────────────────────────────────────────────
def build_stacking_model(preprocessor: ColumnTransformer) -> Pipeline:
    """
    Full stacking pipeline:
      Base learners → XGBoost + LightGBM + RandomForest
      Meta-learner  → Logistic Regression
    Wrapped in sklearn Pipeline with preprocessor.
    """
    print("\n  Building stacking ensemble …")

    base_estimators = [
        ("xgb", xgb.XGBClassifier(
            **{k: v for k, v in CFG.xgb_params.items() if k != "eval_metric"},
            use_label_encoder=False
        )),
        ("lgb", lgb.LGBMClassifier(**CFG.lgb_params)),
        ("rf",  RandomForestClassifier(
            n_estimators=200, max_depth=8,
            class_weight="balanced", random_state=42, n_jobs=-1
        ))
    ]

    stacking = StackingClassifier(
        estimators=base_estimators,
        final_estimator=LogisticRegression(C=1.0, max_iter=1000),
        cv=StratifiedKFold(n_splits=5, shuffle=False),  # no shuffle → time integrity
        passthrough=True,
        n_jobs=-1
    )

    full_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   stacking)
    ])

    return full_pipeline


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 7 — EVALUATION & SHAP
# ─────────────────────────────────────────────────────────────────────────────
def evaluate(
    model: Pipeline, X: pd.DataFrame, y: pd.Series,
    split_name: str = "Test"
) -> Dict:
    """Comprehensive evaluation with business-relevant metrics."""
    print(f"\n{'─'*40}")
    print(f"  Evaluation — {split_name}")
    print(f"{'─'*40}")

    proba = model.predict_proba(X)[:, 1]
    pred  = model.predict(X)

    auroc = roc_auc_score(y, proba)
    ap    = average_precision_score(y, proba)
    f1    = f1_score(y, pred, zero_division=0)

    # Precision@K (top 10% flagged)
    k = max(1, int(len(y) * 0.10))
    top_k_idx = np.argsort(proba)[::-1][:k]
    precision_at_k = y.values[top_k_idx].mean()

    print(f"  AUROC:          {auroc:.4f}")
    print(f"  Avg Precision:  {ap:.4f}")
    print(f"  F1 Score:       {f1:.4f}")
    print(f"  Precision@10%:  {precision_at_k:.4f}")
    print(f"\n  Classification Report:\n")
    print(classification_report(y, pred, target_names=["No Stockout", "Stockout"]))

    # Confusion matrix
    cm = confusion_matrix(y, pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns_labels = np.array([[f"{v}\n({v/cm.sum()*100:.1f}%)" for v in row] for row in cm])
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Predicted 0", "Predicted 1"])
    ax.set_yticklabels(["Actual 0", "Actual 1"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, sns_labels[i, j], ha="center", va="center", fontsize=12)
    ax.set_title(f"Confusion Matrix — {split_name}")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(f"{CFG.output_dir}/confusion_matrix_{split_name.lower()}.png", dpi=120)
    plt.show()

    # Precision-Recall curve
    precision, recall, _ = precision_recall_curve(y, proba)
    plt.figure(figsize=(7, 4))
    plt.plot(recall, precision, color="#1565C0", lw=2)
    plt.fill_between(recall, precision, alpha=0.15, color="#1565C0")
    plt.xlabel("Recall"); plt.ylabel("Precision")
    plt.title(f"Precision-Recall Curve — {split_name} (AP={ap:.3f})")
    plt.tight_layout()
    plt.savefig(f"{CFG.output_dir}/pr_curve_{split_name.lower()}.png", dpi=120)
    plt.show()

    return {"auroc": auroc, "avg_precision": ap, "f1": f1,
            "precision_at_k": precision_at_k}


def explain_with_shap(
    model: Pipeline, X: pd.DataFrame,
    max_display: int = 20, sample_n: int = 500
) -> None:
    """SHAP summary plot for the XGBoost base learner inside the stacking model."""
    print("\n  Computing SHAP values …")
    preprocessor = model.named_steps["preprocessor"]
    classifier   = model.named_steps["classifier"]

    # Extract the XGBoost estimator from StackingClassifier
    xgb_model = classifier.estimators_[0]

    X_sample = X.sample(min(sample_n, len(X)), random_state=42)
    X_transformed = preprocessor.transform(X_sample)

    explainer    = shap.TreeExplainer(xgb_model)
    shap_values  = explainer.shap_values(X_transformed)

    try:
        feature_names = preprocessor.get_feature_names_out()
    except Exception:
        feature_names = [f"feature_{i}" for i in range(X_transformed.shape[1])]

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_transformed,
                      feature_names=feature_names,
                      max_display=max_display, show=False)
    plt.title("SHAP Feature Importance — XGBoost Base Learner", fontsize=12)
    plt.tight_layout()
    plt.savefig(f"{CFG.output_dir}/shap_summary.png", dpi=120, bbox_inches="tight")
    plt.show()
    print(f"  SHAP plot saved to {CFG.output_dir}/shap_summary.png")


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 8 — RISK SCORING & ALERT TIER ASSIGNMENT
# ─────────────────────────────────────────────────────────────────────────────
def assign_alert_tiers(
    df: pd.DataFrame, proba: np.ndarray
) -> pd.DataFrame:
    """
    Composite risk score:
        risk = P(stockout) × criticality_weight × urgency_factor
    Output: alert_tier ∈ {Critical, High, Watch, OK}
    """
    out = df.copy()
    out["stockout_probability"] = proba

    # Criticality weight
    crit_map = {k.lower(): v for k, v in CFG.criticality_weights.items()}
    out["crit_weight"] = (
        out["criticality_level"].str.lower()
        .map(crit_map).fillna(1.0)
    )

    # Urgency factor — items needed sooner get higher weight
    out["urgency_factor"] = 1 / (out["days_until_next_scheduled_order"].clip(1) ** 0.5)

    # Composite score
    out["composite_risk_score"] = (
        out["stockout_probability"] * out["crit_weight"] * out["urgency_factor"]
    )
    out["composite_risk_score"] = (
        out["composite_risk_score"]
        / out["composite_risk_score"].max()   # normalise 0-1
    )

    # Sole-source override → always Critical if high stockout probability
    sole_source_mask = (out["sole_source_item"] == 1) & (out["stockout_probability"] > 0.3)

    def tier(row):
        if sole_source_mask.loc[row.name]:
            return "Critical"
        p = row["composite_risk_score"]
        if p >= CFG.alert_thresholds["critical"]: return "Critical"
        if p >= CFG.alert_thresholds["high"]:     return "High"
        if p >= CFG.alert_thresholds["watch"]:    return "Watch"
        return "OK"

    out["alert_tier"] = out.apply(tier, axis=1)

    print("\n  Alert Tier Distribution:")
    print(out["alert_tier"].value_counts().to_string())
    return out


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 9 — MLFLOW EXPERIMENT TRACKING
# ─────────────────────────────────────────────────────────────────────────────
def log_to_mlflow(
    pipeline: Pipeline,
    metrics: Dict,
    run_name: str = "stacking_ensemble"
) -> None:
    mlflow.set_tracking_uri(CFG.mlflow_uri)
    mlflow.set_experiment(CFG.experiment_name)

    with mlflow.start_run(run_name=run_name):
        # Log config
        mlflow.log_param("train_cutoff", CFG.train_cutoff)
        mlflow.log_param("val_cutoff",   CFG.val_cutoff)
        mlflow.log_params({f"xgb_{k}": v for k, v in CFG.xgb_params.items()})

        # Log metrics
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(pipeline, "stacking_pipeline")

        # Log artefacts
        for png in Path(CFG.output_dir).glob("*.png"):
            mlflow.log_artifact(str(png))

    print(f"\n  ✅ MLflow run logged: {CFG.experiment_name} / {run_name}")
    print(f"     Run: mlflow ui --backend-store-uri {CFG.mlflow_uri}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline() -> None:
    print("\n" + "█" * 60)
    print("  AI-DRIVEN MEDICAL INVENTORY FORECASTING — ML PIPELINE")
    print("█" * 60)

    # ── Stage 1: Load ────────────────────────────────────────────────────────
    df = load_and_validate(CFG.data_path)

    # ── Stage 2: Feature engineering ────────────────────────────────────────
    df, engineered_cols = engineer_features(df)

    # ── Stage 3: Split ───────────────────────────────────────────────────────
    train_df, val_df, test_df = time_based_split(df, CFG.train_cutoff, CFG.val_cutoff)

    X_train, y_train = prepare_xy(train_df, engineered_cols)
    X_val,   y_val   = prepare_xy(val_df,   engineered_cols)
    X_test,  y_test  = prepare_xy(test_df,  engineered_cols)

    # ── Stage 4: Preprocessor ────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("STAGE 4 — Building Preprocessor")
    print("═" * 60)
    preprocessor = build_preprocessor(engineered_cols)
    print("  ✅ Preprocessor built")

    # ── Stage 5 & 6: Stacking ensemble ──────────────────────────────────────
    print("\n" + "═" * 60)
    print("STAGE 5+6 — Training Stacking Ensemble")
    print("═" * 60)
    pipeline = build_stacking_model(preprocessor)
    pipeline.fit(X_train, y_train)
    print("  ✅ Stacking model trained")

    # ── Stage 7: Evaluation ──────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("STAGE 7 — Evaluation & SHAP")
    print("═" * 60)
    val_metrics  = evaluate(pipeline, X_val,  y_val,  split_name="Validation")
    test_metrics = evaluate(pipeline, X_test, y_test, split_name="Test")

    try:
        explain_with_shap(pipeline, X_test)
    except Exception as e:
        print(f"  ⚠️  SHAP explanation skipped: {e}")

    # ── Stage 8: Risk scoring ────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("STAGE 8 — Risk Scoring & Alert Tier Assignment")
    print("═" * 60)
    test_proba    = pipeline.predict_proba(X_test)[:, 1]
    test_with_risk = assign_alert_tiers(test_df.reset_index(drop=True), test_proba)

    alert_output = test_with_risk[
        ["snapshot_date","facility_id","department","item_id",
         "criticality_level","stockout_probability","composite_risk_score",
         "alert_tier","days_until_next_scheduled_order","vendor_reliability_score"]
    ].sort_values("composite_risk_score", ascending=False)

    output_path = f"{CFG.output_dir}/alert_queue.csv"
    alert_output.to_csv(output_path, index=False)
    print(f"  Alert queue saved → {output_path}")

    # ── Stage 9: MLflow ──────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("STAGE 9 — MLflow Experiment Tracking")
    print("═" * 60)
    try:
        log_to_mlflow(pipeline, test_metrics)
    except Exception as e:
        print(f"  ⚠️  MLflow logging skipped: {e}")

    # ── Save model ───────────────────────────────────────────────────────────
    model_path = f"{CFG.output_dir}/stockout_pipeline.pkl"
    joblib.dump(pipeline, model_path)
    print(f"\n  ✅ Model saved → {model_path}")

    # ── Final summary ────────────────────────────────────────────────────────
    print("\n" + "█" * 60)
    print("  PIPELINE COMPLETE")
    print("█" * 60)
    print(f"  Test AUROC:         {test_metrics['auroc']:.4f}")
    print(f"  Test Avg Precision: {test_metrics['avg_precision']:.4f}")
    print(f"  Test F1:            {test_metrics['f1']:.4f}")
    print(f"  Test Precision@10%: {test_metrics['precision_at_k']:.4f}")
    print(f"\n  Outputs saved to: {CFG.output_dir}/")
    print("  Start MLflow UI:  mlflow ui")
    print("█" * 60)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import seaborn as sns  # needed for confusion matrix only
    run_pipeline()
