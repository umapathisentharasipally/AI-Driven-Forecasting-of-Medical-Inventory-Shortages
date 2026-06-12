import pandas as pd
from src.utils.constants import DATE_COLUMN, TARGET_COLUMN

BOOL_MAP = {"yes": 1, "true": 1, "1": 1, "y": 1, "no": 0, "false": 0, "0": 0, "n": 0}


def clean_inventory_data(df: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    data = df.copy()
    data.columns = [c.strip() for c in data.columns]
    if DATE_COLUMN in data.columns:
        data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN], errors="coerce")
    object_cols = data.select_dtypes(include="object").columns
    for col in object_cols:
        data[col] = data[col].astype("string").str.strip()
    for col in ["recent_usage_spike", "active_po_in_transit", "sole_source_item", "substitution_available", "pandemic_or_surge_flag"]:
        if col in data.columns:
            lowered = data[col].astype("string").str.lower().str.strip()
            mapped = lowered.map(BOOL_MAP)
            if mapped.notna().any():
                data[col] = mapped.fillna(data[col])
    if require_target and TARGET_COLUMN in data.columns:
        data[TARGET_COLUMN] = pd.to_numeric(data[TARGET_COLUMN], errors="coerce").fillna(0).astype(int)
    data = data.drop_duplicates().reset_index(drop=True)
    return data
