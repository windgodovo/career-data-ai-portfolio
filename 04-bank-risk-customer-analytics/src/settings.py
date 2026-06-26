from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT_DIR / "sql"
DATA_DIR = ROOT_DIR / "data"
ODS_RAW_DIR = DATA_DIR / "ods_raw"
OUTPUT_DIR = DATA_DIR / "output"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
DB_PATH = WAREHOUSE_DIR / "bank_risk_customer_analytics.duckdb"

SQL_STEPS = [
    "01_ods.sql",
    "02_dwd.sql",
    "03_dws.sql",
    "04_ads.sql",
    "05_serving.sql",
    "06_monitor.sql",
]
