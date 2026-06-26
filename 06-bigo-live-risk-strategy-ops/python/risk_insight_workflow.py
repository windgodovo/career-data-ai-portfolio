"""BIGO LIVE 风控策略运营：Python 分析流程样例。

这个文件是作品集级示例，用于表达如何把 SQL 抽出的特征继续转成洞察：
- 风险突增监控
- 团伙簇识别
- bad case 复盘输入
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.settings import OUTPUT_DIR

ANALYSIS_OUTPUT_DIR = Path(__file__).resolve().parent / "analysis_output"


@dataclass(frozen=True)
class AlertRule:
    metric_name: str
    threshold_ratio: float
    min_count: int


def detect_metric_spike(metric_df: pd.DataFrame, rule: AlertRule) -> pd.DataFrame:
    """Detect daily metric spikes against a 7-day rolling baseline."""
    df = metric_df.sort_values("metric_date").copy()
    df["baseline_7d"] = df[rule.metric_name].rolling(7, min_periods=3).mean().shift(1)
    df["spike_ratio"] = df[rule.metric_name] / df["baseline_7d"]
    return df[
        (df[rule.metric_name] >= rule.min_count)
        & (df["spike_ratio"] >= rule.threshold_ratio)
    ]


def summarize_cluster_risk(cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Rank suspect clusters by size, punishment rate, and report count."""
    df = cluster_df.copy()
    df["cluster_risk_score"] = (
        0.4 * df["user_cnt"].rank(pct=True)
        + 0.35 * df["punish_user_rate"].rank(pct=True)
        + 0.25 * df["report_cnt"].rank(pct=True)
    )
    return df.sort_values("cluster_risk_score", ascending=False)


def build_bad_case_summary(case_row: pd.Series) -> dict[str, str]:
    """Convert one bad case row into a review-friendly summary."""
    return {
        "risk_type": str(case_row.get("risk_type", "unknown")),
        "actor": str(case_row.get("target_id", "unknown")),
        "behavior_chain": str(case_row.get("behavior_chain", "待补充")),
        "suspected_root_cause": str(case_row.get("root_cause", "规则缺失或特征缺失")),
        "next_action": str(case_row.get("next_action", "补充策略并灰度验证")),
    }


def build_risk_event_ranking(bad_case_df: pd.DataFrame) -> pd.DataFrame:
    """Turn review cases into a practical high/medium/low risk event list."""
    df = bad_case_df.copy()

    def risk_level(row: pd.Series) -> str:
        if row.get("root_cause") == "cluster_abuse":
            return "high"
        if row.get("root_cause") == "possible_false_positive" or row.get("review_result") == "normal":
            return "low"
        if row.get("private_message_cnt", 0) >= 3 or row.get("report_cnt_all", 0) >= 1:
            return "medium"
        return "low"

    df["risk_level"] = df.apply(risk_level, axis=1)
    df["risk_score"] = (
        40 * (df["risk_level"] == "high").astype(int)
        + 20 * (df["risk_level"] == "medium").astype(int)
        + 10 * df["report_cnt_all"].rank(pct=True)
        + 10 * df["private_message_cnt"].rank(pct=True)
        + 10 * df["device_user_cnt"].rank(pct=True)
        + 10 * df["payment_amount_sum"].rank(pct=True)
    ).round(2)

    columns = [
        "case_id",
        "target_id",
        "risk_level",
        "risk_score",
        "review_result",
        "appeal_result",
        "root_cause",
        "report_cnt_all",
        "private_message_cnt",
        "device_user_cnt",
        "payment_amount_sum",
    ]
    return df[columns].sort_values(["risk_score", "case_id"], ascending=[False, True])


def write_csv(df: pd.DataFrame, filename: str) -> Path:
    ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ANALYSIS_OUTPUT_DIR / filename
    df.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    metric_path = OUTPUT_DIR / "risk_metric_daily.csv"
    cluster_path = OUTPUT_DIR / "suspect_cluster_result.csv"
    bad_case_path = OUTPUT_DIR / "bad_case_review.csv"

    if not metric_path.exists() or not cluster_path.exists() or not bad_case_path.exists():
        print("Missing output CSVs. Run: python3 scripts/run_pipeline.py")
        raise SystemExit(1)

    metric_df = pd.read_csv(metric_path)
    metric_df["metric_date"] = pd.to_datetime(metric_df["metric_date"])

    cluster_df = pd.read_csv(cluster_path)
    bad_case_df = pd.read_csv(bad_case_path)

    spike_rule = AlertRule(metric_name="punish_cnt", threshold_ratio=1.4, min_count=2)
    spike_df = detect_metric_spike(metric_df, spike_rule)
    ranked_cluster_df = summarize_cluster_risk(cluster_df)
    risk_event_df = build_risk_event_ranking(bad_case_df)

    exported_paths = [
        write_csv(spike_df, "metric_spikes.csv"),
        write_csv(ranked_cluster_df, "ranked_suspect_clusters.csv"),
        write_csv(risk_event_df, "risk_event_ranking.csv"),
        write_csv(risk_event_df[risk_event_df["risk_level"] == "high"], "high_risk_events.csv"),
        write_csv(risk_event_df[risk_event_df["risk_level"] == "medium"], "medium_risk_events.csv"),
        write_csv(risk_event_df[risk_event_df["risk_level"] == "low"], "low_risk_events.csv"),
    ]

    print("[Analysis] Potential metric spikes:")
    if spike_df.empty:
        print("No spike found under current threshold.")
    else:
        print(spike_df.to_string(index=False))

    print("\n[Analysis] Top suspect clusters:")
    print(ranked_cluster_df.head(5).to_string(index=False))

    print("\n[Analysis] High/medium/low risk events:")
    print(risk_event_df.head(8).to_string(index=False))

    if not ranked_cluster_df.empty:
        top_cluster = ranked_cluster_df.iloc[0]
        case = pd.Series(
            {
                "risk_type": "cluster_abuse",
                "target_id": top_cluster.get("cluster_key", "unknown"),
                "behavior_chain": "same device/ip -> reports -> punishment",
                "root_cause": "multi-account cluster needs tighter gating",
                "next_action": "tighten new-account messaging limits for this cluster",
            }
        )
        bad_case_summary_df = pd.DataFrame([build_bad_case_summary(case)])
        exported_paths.append(write_csv(bad_case_summary_df, "bad_case_summary.csv"))
        print("\n[Analysis] Bad case summary:")
        print(bad_case_summary_df.to_string(index=False))

    print("\n[Analysis] CSV outputs:")
    for path in exported_paths:
        print(f"- {path.relative_to(ROOT)}")
