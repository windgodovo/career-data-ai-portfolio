from __future__ import annotations

import pandas as pd


def build_kpis(clean_df: pd.DataFrame) -> dict:
    total_sales = float(clean_df["sales_amount"].sum())
    total_cost = float(clean_df["cost_amount"].sum())
    total_profit = float(clean_df["profit"].sum())
    total_orders = float(clean_df["order_count"].sum())

    by_region = (
        clean_df.groupby("region", as_index=False)[["sales_amount", "cost_amount", "profit", "order_count"]]
        .sum()
        .sort_values("profit", ascending=True)
    )

    by_month = (
        clean_df.groupby("month", as_index=False)[["sales_amount", "cost_amount", "profit", "order_count"]]
        .sum()
        .sort_values("month")
    )

    return {
        "summary": {
            "total_sales": round(total_sales, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "total_orders": int(total_orders),
            "profit_margin": round((total_profit / total_sales) if total_sales else 0.0, 4),
        },
        "by_region": by_region,
        "by_month": by_month,
    }


def make_anomaly_hints(by_region: pd.DataFrame) -> list[str]:
    hints: list[str] = []
    if by_region.empty:
        return ["No data available."]

    worst = by_region.iloc[0]
    hints.append(
        f"Region with lowest profit: {worst['region']} (profit={worst['profit']:.2f})."
    )

    if len(by_region) > 1:
        best = by_region.iloc[-1]
        hints.append(
            f"Region with highest profit: {best['region']} (profit={best['profit']:.2f})."
        )

    return hints
