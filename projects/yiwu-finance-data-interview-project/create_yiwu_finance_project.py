import shutil
import pandas as pd
from pathlib import Path

PROJECT_NAME = "义乌财务数据面试项目"
BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "output"
EXCEL_DIR = BASE_DIR / "excel"
ZIP_PATH = BASE_DIR / f"{PROJECT_NAME}.zip"


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EXCEL_DIR.mkdir(parents=True, exist_ok=True)


def create_excel_file():
    orders = pd.read_csv(RAW_DIR / "order_raw.csv")
    payments = pd.read_csv(RAW_DIR / "pay_raw.csv")
    refunds = pd.read_csv(RAW_DIR / "refund_raw.csv")

    with pd.ExcelWriter(EXCEL_DIR / "yiwu_finance_demo.xlsx", engine="openpyxl") as writer:
        orders.to_excel(writer, sheet_name="order_raw", index=False)
        payments.to_excel(writer, sheet_name="pay_raw", index=False)
        refunds.to_excel(writer, sheet_name="refund_raw", index=False)


def make_zip():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    shutil.make_archive(str(ZIP_PATH.with_suffix("")), "zip", BASE_DIR)


def main():
    ensure_dirs()
    create_excel_file()
    make_zip()
    print("创建完成：")
    print(EXCEL_DIR / "yiwu_finance_demo.xlsx")
    print(ZIP_PATH)


if __name__ == "__main__":
    main()
