from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.settings import DB_PATH, ROOT_DIR, SQL_DIR, SQL_STEPS, WAREHOUSE_DIR

CSV_OUT_DIR = Path(__file__).resolve().parent / "csv_preview"


@dataclass(frozen=True)
class TableInfo:
    name: str
    source: str
    order_by: str | None = None


STEP_TABLES: dict[str, list[TableInfo]] = {
    "01_ods.sql": [
        TableInfo("ods.vehicle_profile", "data/ods_raw/vehicle_profile.csv", "vehicle_id"),
        TableInfo("ods.charger_station", "data/ods_raw/charger_station.csv", "station_id"),
        TableInfo("ods.charge_order", "data/ods_raw/charge_order.csv", "order_id"),
        TableInfo("ods.payment_txn", "data/ods_raw/payment_txn.csv", "payment_id"),
        TableInfo("ods.station_ops_snapshot", "data/ods_raw/station_ops_snapshot.csv", "station_id"),
    ],
    "02_dwd.sql": [
        TableInfo("dwd.dim_vehicle", "ods.vehicle_profile", "vehicle_id"),
        TableInfo("dwd.dim_station", "ods.charger_station", "station_id"),
        TableInfo("dwd.fact_charge_order", "ods.charge_order where status = COMPLETED", "order_id"),
        TableInfo("dwd.fact_payment", "ods.payment_txn where is_success = 1", "payment_id"),
        TableInfo("dwd.fact_station_ops", "ods.station_ops_snapshot", "station_id"),
    ],
    "03_dws.sql": [
        TableInfo("dws.station_performance_7d", "dwd.fact_charge_order + dwd.fact_payment", "station_id"),
        TableInfo("dws.vehicle_station_preference_30d", "dwd.fact_charge_order + dwd.fact_payment", "vehicle_id, station_id"),
    ],
    "04_ads.sql": [
        TableInfo("ads.station_supply_demand_score", "dwd.dim_station + dws.station_performance_7d + dwd.fact_station_ops", "station_id"),
    ],
    "05_features.sql": [
        TableInfo("feature.vehicle_station_preference_wide", "dwd.dim_vehicle x dwd.dim_station + dws.vehicle_station_preference_30d + ads.station_supply_demand_score", "vehicle_id, recommend_score DESC"),
    ],
    "06_serving.sql": [
        TableInfo("serving.charge_reco_topn", "feature.vehicle_station_preference_wide, ranked by recommend_score", "vehicle_id, rank_no"),
    ],
    "07_monitor.sql": [
        TableInfo("monitor.data_quality_report", "dwd.fact_charge_order + serving.charge_reco_topn checks", "check_item"),
    ],
}


def _run_sql_step(conn: duckdb.DuckDBPyConnection, sql_name: str) -> None:
    sql_path = SQL_DIR / sql_name
    sql_text = sql_path.read_text(encoding="utf-8").replace("{{ROOT}}", str(ROOT_DIR))
    conn.execute(sql_text)


def _export_table_csv(conn: duckdb.DuckDBPyConnection, info: TableInfo, step_index: int) -> None:
    order_clause = f" ORDER BY {info.order_by}" if info.order_by else ""
    df = conn.execute(f"SELECT * FROM {info.name}{order_clause}").df()
    # e.g. step 2, dwd.fact_charge_order -> 02_dwd__fact_charge_order.csv
    filename = f"{step_index:02d}_{info.name.replace('.', '__')}.csv"
    csv_path = CSV_OUT_DIR / filename
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"  [CSV] {csv_path.relative_to(ROOT)}  ({len(df)} rows)")


def main() -> None:
    CSV_OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Remove old CSV files before regenerating
    for old in CSV_OUT_DIR.glob("*.csv"):
        old.unlink()
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
                _export_table_csv(conn, info, step_index)
    finally:
        conn.close()

    print(f"\nAll CSVs saved to: {CSV_OUT_DIR}")


if __name__ == "__main__":
    main()
