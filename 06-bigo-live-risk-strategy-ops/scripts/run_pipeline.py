from __future__ import annotations

from pathlib import Path
import sys

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.settings import DB_PATH, OUTPUT_DIR, ROOT_DIR, SQL_DIR, SQL_STEPS, WAREHOUSE_DIR

EXPORT_TABLES: list[tuple[str, str]] = [
    ("ads.risk_account_features", "risk_account_features.csv"),
    ("ads.risk_room_features", "risk_room_features.csv"),
    ("ads.reused_content_template", "reused_content_template.csv"),
    ("ads.suspect_cluster_result", "suspect_cluster_result.csv"),
    ("ads.behavior_chain_features", "behavior_chain_features.csv"),
    ("ads.payment_flow_risk", "payment_flow_risk.csv"),
    ("serving.risk_strategy_candidate", "risk_strategy_candidate.csv"),
    ("monitor.risk_metric_daily", "risk_metric_daily.csv"),
    ("monitor.bad_case_review", "bad_case_review.csv"),
    ("monitor.strategy_effect_snapshot", "strategy_effect_snapshot.csv"),
]


def _render_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("{{ROOT}}", str(ROOT_DIR))


def main() -> None:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH))
    try:
        for step in SQL_STEPS:
            sql_path = SQL_DIR / step
            conn.execute(_render_sql(sql_path))
            print(f"[OK] executed {sql_path}")

        for table_name, file_name in EXPORT_TABLES:
            df = conn.execute(f"SELECT * FROM {table_name}").df()
            output_path = OUTPUT_DIR / file_name
            df.to_csv(output_path, index=False, encoding="utf-8")
            print(f"[CSV] {output_path.relative_to(ROOT)} ({len(df)} rows)")

        print("\nPipeline completed successfully.")
        print(f"DuckDB file: {DB_PATH}")
        print(f"Output dir: {OUTPUT_DIR}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
