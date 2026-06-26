"""金铲铲 DA：Python 分析示例。

用于展示版本分析、阵容平衡和基础模型的分析思路。
实际项目中可读取 SQL 导出的 CSV 或连接数仓表。
"""

from __future__ import annotations

import pandas as pd


def compare_patch_comp_performance(df: pd.DataFrame, before: str, after: str) -> pd.DataFrame:
    """Compare comp top4/win/pick metrics before and after a patch."""
    metric = (
        df.groupby(["patch_version", "final_comp_id"])
        .agg(
            play_cnt=("match_id", "count"),
            top4_rate=("rank_no", lambda s: (s <= 4).mean()),
            win_rate=("rank_no", lambda s: (s == 1).mean()),
            avg_rank=("rank_no", "mean"),
        )
        .reset_index()
    )
    before_df = metric[metric["patch_version"] == before].drop(columns="patch_version")
    after_df = metric[metric["patch_version"] == after].drop(columns="patch_version")
    result = before_df.merge(after_df, on="final_comp_id", how="outer", suffixes=("_before", "_after")).fillna(0)
    result["top4_delta"] = result["top4_rate_after"] - result["top4_rate_before"]
    result["win_delta"] = result["win_rate_after"] - result["win_rate_before"]
    result["pick_delta"] = result["play_cnt_after"] - result["play_cnt_before"]
    return result.sort_values("top4_delta")


def flag_balance_risk(comp_metric: pd.DataFrame) -> pd.DataFrame:
    """Flag comps that may be too strong, too weak, or too concentrated."""
    df = comp_metric.copy()
    df["balance_flag"] = "normal"
    df.loc[(df["pick_rate"] >= 0.15) & (df["top4_rate"] >= 0.58), "balance_flag"] = "overpowered"
    df.loc[(df["pick_rate"] <= 0.03) & (df["top4_rate"] <= 0.45), "balance_flag"] = "underpowered"
    df.loc[(df["pick_rate"] <= 0.05) & (df["top4_rate"] >= 0.58), "balance_flag"] = "hidden_strong"
    return df


def simple_churn_features(player_daily: pd.DataFrame) -> pd.DataFrame:
    """Build simple churn features for DA interview demonstration."""
    agg = (
        player_daily.groupby("player_id")
        .agg(
            login_days_7d=("login_flag", "sum"),
            match_cnt_7d=("match_cnt", "sum"),
            pay_amount_7d=("pay_amount", "sum"),
            last_login_date=("dt", "max"),
        )
        .reset_index()
    )
    agg["low_activity_flag"] = (agg["login_days_7d"] <= 2).astype(int)
    return agg


if __name__ == "__main__":
    print("Golden Spatula DA analysis examples. Connect exported match/player data to run.")
