from __future__ import annotations
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from ..preprocessing.encoding import one_hot_encoder
from ..preprocessing.missing_value_handler import categorical_imputer, numeric_imputer
from ..preprocessing.scaling import standard_scaler


def infer_feature_columns(df: pd.DataFrame, excluded_columns: list[str]) -> tuple[list[str], list[str]]:
    X = df.drop(columns=excluded_columns, errors="ignore")
    numeric_cols = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    return numeric_cols, categorical_cols


def build_preprocessing_pipeline(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(steps=[("imputer", numeric_imputer()), ("scaler", standard_scaler())])
    categorical_pipeline = Pipeline(steps=[("imputer", categorical_imputer()), ("onehot", one_hot_encoder())])
    return ColumnTransformer(
        transformers=[("num", numeric_pipeline, numeric_cols), ("cat", categorical_pipeline, categorical_cols)],
        remainder="drop",
        verbose_feature_names_out=False,
    )
