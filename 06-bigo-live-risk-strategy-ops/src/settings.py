from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT_DIR / "sql"
WAREHOUSE_DIR = ROOT_DIR / "data" / "warehouse"
OUTPUT_DIR = ROOT_DIR / "data" / "output"
DB_PATH = WAREHOUSE_DIR / "bigo_live_risk_strategy.duckdb"

SQL_STEPS = [
    "01_ods.sql",
    "02_ads.sql",
    "03_monitor.sql",
]
