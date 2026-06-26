from __future__ import annotations

from pathlib import Path
import sys

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.settings import DB_PATH, OUTPUT_DIR, ROOT_DIR, SQL_DIR, SQL_STEPS, WAREHOUSE_DIR


def _run_sql_steps(conn: duckdb.DuckDBPyConnection) -> None:
    for name in SQL_STEPS:
        sql_path = SQL_DIR / name
        sql_text = sql_path.read_text(encoding="utf-8").replace("{{ROOT}}", str(ROOT_DIR))
        conn.execute(sql_text)
        print(f"[OK] {name}")


def _export_outputs(conn: duckdb.DuckDBPyConnection) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reco_df = conn.execute(
        "SELECT * FROM serving.charge_reco_topn ORDER BY vehicle_id, rank_no"
    ).df()
    reco_df.to_csv(OUTPUT_DIR / "charge_reco_topn.csv", index=False)

    feature_df = conn.execute(
        "SELECT * FROM feature.vehicle_station_preference_wide ORDER BY vehicle_id, recommend_score DESC"
    ).df()
    feature_df.to_csv(OUTPUT_DIR / "vehicle_station_preference_wide.csv", index=False)

    monitor_df = conn.execute(
        "SELECT * FROM monitor.data_quality_report"
    ).df()
    monitor_df.to_csv(OUTPUT_DIR / "data_quality_report.csv", index=False)

    print("[OK] export charge_reco_topn.csv")
    print("[OK] export vehicle_station_preference_wide.csv")
    print("[OK] export data_quality_report.csv")


if __name__ == "__main__":
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    try:
        _run_sql_steps(conn)
        _export_outputs(conn)

        preview = conn.execute(
            "SELECT * FROM serving.charge_reco_topn ORDER BY vehicle_id, rank_no LIMIT 15"
        ).fetchdf()
        print("\n=== Recommendation Preview ===")
        print(preview.to_string(index=False))
    finally:
        conn.close()
