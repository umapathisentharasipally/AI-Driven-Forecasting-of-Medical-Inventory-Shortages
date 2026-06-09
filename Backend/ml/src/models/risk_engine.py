from __future__ import annotations
import numpy as np
import pandas as pd


def classify_risk(score: float, thresholds: dict) -> str:
    if score >= thresholds.get("high", 0.8):
        return "High"
    if score >= thresholds.get("medium", 0.6):
        return "Medium"
    if score >= thresholds.get("low", 0.3):
        return "Low"
    return "Very Low"


def apply_risk_engine(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    data = df.copy()
    thresholds = config.get("risk_thresholds", {})
    weights = config.get("weights", {})
    rules = config.get("business_rules", {})
    probability = data.get("stockout_probability", pd.Series(0, index=data.index)).astype(float).clip(0, 1)
    days_supply = data.get("days_of_supply_on_hand", pd.Series(np.nan, index=data.index)).astype(float)
    days_supply_risk = (1 - (days_supply / 30).clip(0, 1)).fillna(0)
    vendor_reliability = data.get("vendor_reliability_score", pd.Series(1, index=data.index)).astype(float).clip(0, 1)
    vendor_risk = 1 - vendor_reliability
    anomaly_risk = data.get("is_anomaly", pd.Series(0, index=data.index)).astype(int).clip(0, 1)
    risk_score = (
        weights.get("stockout_probability", 0.55) * probability
        + weights.get("days_supply_risk", 0.20) * days_supply_risk
        + weights.get("vendor_risk", 0.15) * vendor_risk
        + weights.get("anomaly_risk", 0.10) * anomaly_risk
    )
    if "criticality_level" in data.columns:
        boost_map = rules.get("criticality_boost", {})
        risk_score += data["criticality_level"].astype(str).map(boost_map).fillna(0)
    if "active_po_in_transit" in data.columns:
        active_po = data["active_po_in_transit"].astype(str).str.lower().isin(["1", "true", "yes"])
        risk_score -= active_po.astype(float) * rules.get("active_po_reduction", 0.05)
    data["business_risk_score"] = risk_score.clip(0, 1)
    data["business_risk_level"] = data["business_risk_score"].apply(lambda x: classify_risk(float(x), thresholds))
    return data
