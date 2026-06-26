from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import duckdb

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.settings import DB_PATH, ROOT_DIR, SQL_DIR, SQL_STEPS, WAREHOUSE_DIR

CSV_PREVIEW_DIR = Path(__file__).resolve().parent / "csv_preview"


@dataclass(frozen=True)
class TableInfo:
    name: str
    source: str
    order_by: str | None = None


STEP_TABLES: dict[str, list[TableInfo]] = {
    "01_ods.sql": [
        TableInfo("ods.customer", "data/ods_raw/customer.csv", "customer_id"),
        TableInfo("ods.account", "data/ods_raw/account.csv", "account_id"),
        TableInfo("ods.transaction", "data/ods_raw/transaction.csv", "txn_id"),
        TableInfo("ods.credit_limit", "data/ods_raw/credit_limit.csv", "customer_id"),
        TableInfo("ods.overdue_record", "data/ods_raw/overdue_record.csv", "overdue_id"),
    ],
    "02_dwd.sql": [
        TableInfo("dwd.dim_customer", "ods.customer", "customer_id"),
        TableInfo("dwd.dim_account", "ods.account", "account_id"),
        TableInfo("dwd.fact_transaction", "ods.transaction", "txn_id"),
        TableInfo("dwd.fact_credit_snapshot", "ods.credit_limit", "customer_id"),
        TableInfo("dwd.fact_overdue_record", "ods.overdue_record", "overdue_id"),
    ],
    "03_dws.sql": [
        TableInfo("dws.customer_transaction_baseline", "dwd.fact_transaction + dwd.dim_account", "customer_id"),
        TableInfo("dws.customer_most_used_channel", "dwd.fact_transaction", "customer_id"),
        TableInfo("dws.customer_behavior_30d", "dwd.fact_transaction + dwd.dim_account", "customer_id"),
        TableInfo("dws.customer_risk_features_30d", "dws + dwd credit/overdue/account", "customer_id"),
    ],
    "04_ads.sql": [
        TableInfo("ads.customer_risk_score", "dws.customer_risk_features_30d", "risk_score DESC"),
        TableInfo("ads.customer_segment", "dws.customer_behavior_30d + ads.customer_risk_score", "customer_id"),
        TableInfo("ads.abnormal_transaction_detail", "dwd.fact_transaction + dws baselines", "txn_time DESC"),
    ],
    "05_serving.sql": [
        TableInfo("serving.high_risk_customer_list", "ads.customer_risk_score + dwd.dim_customer", "risk_score DESC"),
        TableInfo("serving.customer_segment_result", "ads.customer_segment + dwd.dim_customer", "customer_segment, risk_score DESC"),
        TableInfo("serving.abnormal_txn_alert_list", "ads.abnormal_transaction_detail + dwd.dim_customer", "severity DESC, amount DESC"),
    ],
    "06_monitor.sql": [
        TableInfo("monitor.data_quality_report", "dwd + ads integrity checks", "check_item"),
        TableInfo("monitor.risk_metric_daily_report", "dwd + ads + monitor aggregate metrics", None),
    ],
}


def _run_sql_step(conn: duckdb.DuckDBPyConnection, sql_name: str) -> None:
    sql_path = SQL_DIR / sql_name
    sql_text = sql_path.read_text(encoding="utf-8").replace("{{ROOT}}", str(ROOT_DIR))
    conn.execute(sql_text)


def _print_table_preview(conn: duckdb.DuckDBPyConnection, info: TableInfo, limit: int) -> None:
    row_count = conn.execute(f"SELECT COUNT(*) FROM {info.name}").fetchone()[0]
    order_clause = f" ORDER BY {info.order_by}" if info.order_by else ""
    preview = conn.execute(f"SELECT * FROM {info.name}{order_clause} LIMIT {limit}").df()

    print(f"\n  Table: {info.name}")
    print(f"  Source: {info.source}")
    print(f"  Rows: {row_count}")
    print("  Preview:")
    if preview.empty:
        print("    (no rows)")
    else:
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
            print(f"[OK] executed {SQL_DIR / sql_name}")

            for info in STEP_TABLES.get(sql_name, []):
                _print_table_preview(conn, info, limit=5)
                _export_table_csv(conn, info, step_index)
    finally:
        conn.close()

    print(f"\nAll table CSVs saved to: {CSV_PREVIEW_DIR}")


if __name__ == "__main__":
    main()
