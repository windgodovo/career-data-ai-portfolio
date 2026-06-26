from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import duckdb

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.settings import DB_PATH, ROOT_DIR, SQL_DIR, SQL_STEPS, WAREHOUSE_DIR

CSV_PREVIEW_DIR = Path(__file__).resolve().parent / "csv_preview"


@dataclass(frozen=True)
class TableInfo:
    name: str
    source: str
    order_by: str | None = None


STEP_TABLES: dict[str, list[TableInfo]] = {
    "01_ods.sql": [
        TableInfo("ods.account_behavior", "data/ods_raw/account_behavior.csv", "user_id"),
        TableInfo("ods.room_event", "data/ods_raw/room_event.csv", "start_time DESC"),
        TableInfo("ods.message_event", "data/ods_raw/message_event.csv", "send_time DESC"),
        TableInfo("ods.report_event", "data/ods_raw/report_event.csv", "report_time DESC"),
        TableInfo("ods.review_event", "data/ods_raw/review_event.csv", "review_time DESC"),
        TableInfo("ods.punishment_event", "data/ods_raw/punishment_event.csv", "punish_time DESC"),
        TableInfo("ods.payment_order", "data/ods_raw/payment_order.csv", "order_time DESC"),
    ],
    "02_ads.sql": [
        TableInfo("ads.risk_account_features", "ods account/message/report/punishment", "punish_cnt_all DESC, user_id"),
        TableInfo("ads.risk_room_features", "ods room/message/report/punishment", "report_cnt DESC, room_id"),
        TableInfo("ads.reused_content_template", "ods.message_event template aggregation", "message_cnt DESC, normalized_content"),
        TableInfo("ads.suspect_cluster_result", "ods.account + report + punishment", "punish_user_rate DESC, user_cnt DESC"),
        TableInfo("ads.behavior_chain_features", "ods.message_event + payment_order", "payment_amount_sum DESC, user_id"),
        TableInfo("ads.payment_flow_risk", "ods.payment_order payment category aggregation", "amount_sum DESC, payment_subject"),
        TableInfo("serving.risk_strategy_candidate", "ads.risk_account_features candidate rules", "report_cnt_all DESC, user_id"),
    ],
    "03_monitor.sql": [
        TableInfo("monitor.risk_metric_daily", "ods.punishment_event daily aggregate", "metric_date DESC, punish_cnt DESC"),
        TableInfo("monitor.bad_case_review", "ods.review_event + ads.risk_account_features", "review_time DESC"),
        TableInfo("monitor.strategy_effect_snapshot", "ads summary metrics", "snapshot_date DESC"),
    ],
}


def _render_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("{{ROOT}}", str(ROOT_DIR))


def _run_sql_step(conn: duckdb.DuckDBPyConnection, sql_name: str) -> None:
    sql_path = SQL_DIR / sql_name
    conn.execute(_render_sql(sql_path))
    print(f"[OK] executed {sql_path}")


def _print_table_preview(conn: duckdb.DuckDBPyConnection, info: TableInfo, limit: int) -> None:
    order_clause = f" ORDER BY {info.order_by}" if info.order_by else ""
    count_sql = f"SELECT COUNT(*) AS cnt FROM {info.name}"
    preview_sql = f"SELECT * FROM {info.name}{order_clause} LIMIT {limit}"

    row_cnt = conn.execute(count_sql).fetchone()[0]
    preview = conn.execute(preview_sql).df()

    print(f"\n  Table: {info.name}")
    print(f"  Source: {info.source}")
    print(f"  Rows: {row_cnt}")
    if preview.empty:
        print("  Preview: <empty>")
    else:
        print("  Preview:")
        for line in preview.to_string(index=False).splitlines():
            print(f"    {line}")


def _export_table_csv(conn: duckdb.DuckDBPyConnection, info: TableInfo, step_index: int) -> None:
    order_clause = f" ORDER BY {info.order_by}" if info.order_by else ""
    df = conn.execute(f"SELECT * FROM {info.name}{order_clause}").df()
    filename = f"{step_index:02d}_{info.name.replace('.', '__')}.csv"
    csv_path = CSV_PREVIEW_DIR / filename
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  [CSV] {csv_path.relative_to(ROOT)} ({len(df)} rows)")


def main() -> None:
    CSV_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for old_csv in CSV_PREVIEW_DIR.glob("*.csv"):
        old_csv.unlink()

    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))

    try:
        for step_index, sql_name in enumerate(SQL_STEPS, start=1):
            print("\n" + "=" * 88)
            print(f"Step {step_index}: {sql_name}")
            print("=" * 88)
            _run_sql_step(conn, sql_name)

            for info in STEP_TABLES.get(sql_name, []):
                _print_table_preview(conn, info, limit=5)
                _export_table_csv(conn, info, step_index)
    finally:
        conn.close()

    print(f"\nAll table CSVs saved to: {CSV_PREVIEW_DIR}")


if __name__ == "__main__":
    main()
