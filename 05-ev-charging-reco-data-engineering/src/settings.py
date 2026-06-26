from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT_DIR / "sql"
WAREHOUSE_DIR = ROOT_DIR / "data" / "warehouse"
OUTPUT_DIR = ROOT_DIR / "data" / "output"
DB_PATH = WAREHOUSE_DIR / "charging_reco.duckdb"

SQL_STEPS = [
    "01_ods.sql",
    "02_dwd.sql",
    "03_dws.sql",
    "04_ads.sql",
    "05_features.sql",
    "06_serving.sql",
    "07_monitor.sql",
]
