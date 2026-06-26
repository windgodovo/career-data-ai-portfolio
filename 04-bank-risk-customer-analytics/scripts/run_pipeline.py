from __future__ import annotations

from pathlib import Path
import sys

import duckdb

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.settings import DB_PATH, OUTPUT_DIR, ROOT_DIR, SQL_DIR, SQL_STEPS, WAREHOUSE_DIR


def _run_sql_step(conn: duckdb.DuckDBPyConnection, sql_name: str) -> None:
    sql_path = SQL_DIR / sql_name
    sql_text = sql_path.read_text(encoding="utf-8").replace("{{ROOT}}", str(ROOT_DIR))
    conn.execute(sql_text)


def _export_outputs(conn: duckdb.DuckDBPyConnection) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn.execute(
        """
        COPY (SELECT * FROM serving.high_risk_customer_list ORDER BY risk_score DESC)
        TO ? (HEADER, DELIMITER ',');
        """,
        [str(OUTPUT_DIR / "high_risk_customer_list.csv")],
    )

    conn.execute(
        """
        COPY (SELECT * FROM serving.customer_segment_result ORDER BY customer_segment, risk_score DESC)
        TO ? (HEADER, DELIMITER ',');
        """,
        [str(OUTPUT_DIR / "customer_segment_result.csv")],
    )

    conn.execute(
        """
        COPY (SELECT * FROM serving.abnormal_txn_alert_list ORDER BY severity DESC, amount DESC)
        TO ? (HEADER, DELIMITER ',');
        """,
        [str(OUTPUT_DIR / "abnormal_txn_alert_list.csv")],
    )

    conn.execute(
        """
        COPY (SELECT * FROM monitor.data_quality_report ORDER BY check_item)
        TO ? (HEADER, DELIMITER ',');
        """,
        [str(OUTPUT_DIR / "data_quality_report.csv")],
    )

    conn.execute(
        """
        COPY (SELECT * FROM monitor.risk_metric_daily_report)
        TO ? (HEADER, DELIMITER ',');
        """,
        [str(OUTPUT_DIR / "risk_metric_daily_report.csv")],
    )


def _print_preview(conn: duckdb.DuckDBPyConnection) -> None:
    print("\n=== High Risk Customers ===")
    print(conn.execute("SELECT * FROM serving.high_risk_customer_list LIMIT 10").df().to_string(index=False))

    print("\n=== Customer Segment Distribution ===")
    print(
        conn.execute(
            """
            SELECT customer_segment, COUNT(*) AS customer_cnt
            FROM serving.customer_segment_result
            GROUP BY customer_segment
            ORDER BY customer_cnt DESC, customer_segment
            """
        ).df().to_string(index=False)
    )

    print("\n=== Abnormal Transaction Alerts (Top 10) ===")
    print(conn.execute("SELECT * FROM serving.abnormal_txn_alert_list LIMIT 10").df().to_string(index=False))

    print("\n=== Data Quality Report ===")
    print(conn.execute("SELECT * FROM monitor.data_quality_report ORDER BY check_item").df().to_string(index=False))



def main() -> None:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH))
    try:
        for idx, sql_name in enumerate(SQL_STEPS, start=1):
            print("\n" + "=" * 80)
            print(f"Step {idx}: {sql_name}")
            print("=" * 80)
            _run_sql_step(conn, sql_name)
            print(f"[OK] executed {SQL_DIR / sql_name}")

        _export_outputs(conn)
        _print_preview(conn)

        print(f"\n[OK] outputs exported to: {OUTPUT_DIR}")
        print(f"[OK] warehouse file: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
