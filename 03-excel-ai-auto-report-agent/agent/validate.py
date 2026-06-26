from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ValidationResult:
    clean_df: pd.DataFrame
    invalid_df: pd.DataFrame


def validate_frame(df: pd.DataFrame) -> ValidationResult:
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")

    numeric_cols = ["sales_amount", "cost_amount", "order_count"]
    for col in numeric_cols:
        tmp[col] = pd.to_numeric(tmp[col], errors="coerce")

    invalid_mask = (
        tmp["date"].isna()
        | tmp["region"].isna()
        | (tmp["sales_amount"] < 0)
        | (tmp["cost_amount"] < 0)
        | (tmp["order_count"] < 0)
        | tmp[numeric_cols].isna().any(axis=1)
    )

    invalid_df = tmp[invalid_mask].copy()
    clean_df = tmp[~invalid_mask].copy()

    clean_df["profit"] = clean_df["sales_amount"] - clean_df["cost_amount"]
    clean_df["month"] = clean_df["date"].dt.to_period("M").astype(str)

    return ValidationResult(clean_df=clean_df, invalid_df=invalid_df)
