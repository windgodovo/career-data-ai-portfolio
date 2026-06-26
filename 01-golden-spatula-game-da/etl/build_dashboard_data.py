from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "output"

BEFORE_PATCH = "S11.3"
AFTER_PATCH = "S11.4"


def build_comp_meta_summary(comp_daily: pd.DataFrame) -> pd.DataFrame:
    latest_patch = comp_daily["patch_version"].max()
    latest_dt = comp_daily.loc[comp_daily["patch_version"] == latest_patch, "dt"].max()
    latest = comp_daily[(comp_daily["patch_version"] == latest_patch) & (comp_daily["dt"] == latest_dt)].copy()
    total_play_cnt = latest["play_cnt"].sum()
    total_top4_cnt = latest["top4_cnt"].sum()
    total_win_cnt = latest["win_cnt"].sum()

    latest["pick_rate"] = latest["play_cnt"] / total_play_cnt
    latest["top4_rate"] = latest["top4_cnt"] / latest["play_cnt"]
    latest["win_rate"] = latest["win_cnt"] / latest["play_cnt"]
    latest["top4_share"] = latest["top4_cnt"] / total_top4_cnt
    latest["win_share"] = latest["win_cnt"] / total_win_cnt
    latest["meta_flag"] = "normal"
    latest.loc[(latest["pick_rate"] >= 0.18) & (latest["top4_rate"] >= 0.58), "meta_flag"] = "overpowered"
    latest.loc[(latest["pick_rate"] <= 0.08) & (latest["top4_rate"] <= 0.48), "meta_flag"] = "underpowered"
    latest.loc[(latest["pick_rate"] <= 0.10) & (latest["top4_rate"] >= 0.58), "meta_flag"] = "hidden_strong"

    columns = [
        "dt",
        "patch_version",
        "region",
        "rank_tier",
        "comp_id",
        "comp_name",
        "tier",
        "play_cnt",
        "pick_rate",
        "top4_rate",
        "win_rate",
        "top4_share",
        "win_share",
        "avg_rank",
        "meta_flag",
    ]
    return latest[columns].sort_values(["win_share", "top4_share"], ascending=False)


def build_patch_delta(comp_daily: pd.DataFrame) -> pd.DataFrame:
    patch_metric = (
        comp_daily.groupby(["patch_version", "comp_id", "comp_name"], as_index=False)
        .agg(
            play_cnt=("play_cnt", "sum"),
            top4_cnt=("top4_cnt", "sum"),
            win_cnt=("win_cnt", "sum"),
            avg_rank=("avg_rank", "mean"),
        )
    )
    patch_metric["top4_rate"] = patch_metric["top4_cnt"] / patch_metric["play_cnt"]
    patch_metric["win_rate"] = patch_metric["win_cnt"] / patch_metric["play_cnt"]

    before = patch_metric[patch_metric["patch_version"] == BEFORE_PATCH].drop(columns="patch_version")
    after = patch_metric[patch_metric["patch_version"] == AFTER_PATCH].drop(columns="patch_version")
    delta = before.merge(after, on=["comp_id", "comp_name"], how="outer", suffixes=("_before", "_after")).fillna(0)
    delta["play_delta"] = delta["play_cnt_after"] - delta["play_cnt_before"]
    delta["top4_delta"] = delta["top4_rate_after"] - delta["top4_rate_before"]
    delta["win_delta"] = delta["win_rate_after"] - delta["win_rate_before"]
    delta["avg_rank_delta"] = delta["avg_rank_after"] - delta["avg_rank_before"]
    delta["patch_reading"] = "watch"
    delta.loc[(delta["top4_delta"] >= 0.035) & (delta["play_delta"] >= 500), "patch_reading"] = "buff_effective"
    delta.loc[(delta["top4_delta"] <= -0.035) & (delta["play_delta"] <= -500), "patch_reading"] = "nerf_effective"
    delta.loc[(delta["win_delta"] >= 0.025) & (delta["play_delta"] >= 800), "patch_reading"] = "meta_rising"
    return delta.sort_values("top4_delta", ascending=False)


def build_migration_summary(migration: pd.DataFrame) -> pd.DataFrame:
    total = migration["player_cnt"].sum()
    df = migration.copy()
    df["migration_share"] = df["player_cnt"] / total
    return df.sort_values("player_cnt", ascending=False)


def build_unit_item_risk(unit_item: pd.DataFrame) -> pd.DataFrame:
    df = unit_item.copy()
    df["balance_flag"] = "normal"
    df.loc[(df["appear_cnt"] >= 3500) & (df["top4_rate"] >= 0.59), "balance_flag"] = "overpowered_item_binding"
    df.loc[(df["appear_cnt"] <= 2000) & (df["top4_rate"] <= 0.49), "balance_flag"] = "underpowered_core"
    return df.sort_values(["top4_rate", "appear_cnt"], ascending=False)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    comp_daily = pd.read_csv(RAW_DIR / "comp_daily_metrics.csv", parse_dates=["dt"])
    unit_item = pd.read_csv(RAW_DIR / "unit_item_metrics.csv")
    migration = pd.read_csv(RAW_DIR / "meta_migration.csv")

    outputs = {
        "comp_meta_summary.csv": build_comp_meta_summary(comp_daily),
        "patch_delta_summary.csv": build_patch_delta(comp_daily),
        "meta_migration_summary.csv": build_migration_summary(migration),
        "unit_item_risk.csv": build_unit_item_risk(unit_item),
    }

    for filename, df in outputs.items():
        output_path = OUTPUT_DIR / filename
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"[CSV] {output_path.relative_to(ROOT)} ({len(df)} rows)")


if __name__ == "__main__":
    main()
