import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_date(value):
    """兼容 2025/1/1、2025-01-01、20250102 等日期格式。"""
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    return pd.to_datetime(text, errors="coerce")


def clean_money(value):
    """清洗 ¥1,200、 ¥75 这类金额文本，并转成 float。"""
    if pd.isna(value):
        return 0.0
    text = str(value).replace("¥", "").replace(",", "").strip()
    if text == "":
        return 0.0
    return float(text)


def load_data():
    orders = pd.read_csv(RAW_DIR / "order_raw.csv")
    payments = pd.read_csv(RAW_DIR / "pay_raw.csv")
    refunds = pd.read_csv(RAW_DIR / "refund_raw.csv")
    return orders, payments, refunds


def clean_orders(orders):
    cleaning_logs = []

    before = len(orders)
    orders = orders.dropna(how="all")
    after = len(orders)
    if before > after:
        cleaning_logs.append({
            "问题类型": "空行",
            "影响行数": before - after,
            "处理方式": "删除整行为空的数据",
        })

    before = len(orders)
    orders = orders.drop_duplicates(subset=["订单号"], keep="first")
    after = len(orders)
    if before > after:
        cleaning_logs.append({
            "问题类型": "重复订单",
            "影响行数": before - after,
            "处理方式": "按订单号去重，保留第一条记录",
        })

    orders["下单日期"] = orders["下单日期"].apply(parse_date)
    for col in ["订单金额", "运费"]:
        orders[col] = orders[col].apply(clean_money)

    for col in ["店铺", "SKU", "商品名称", "省份", "订单状态"]:
        orders[col] = orders[col].astype(str).str.strip()

    province_map = {
        "浙冮": "浙江",
        "浙江": "浙江",
        "廣东": "广东",
        "广东": "广东",
        "江苏": "江苏",
        "上海": "上海",
    }
    orders["省份"] = orders["省份"].replace(province_map)

    return orders, pd.DataFrame(cleaning_logs)


def clean_payments(payments):
    payments["支付日期"] = payments["支付日期"].apply(parse_date)
    payments["实收金额"] = payments["实收金额"].apply(clean_money)
    payments["平台手续费"] = payments["平台手续费"].apply(clean_money)
    payments["支付渠道"] = payments["支付渠道"].astype(str).str.strip()
    return payments


def clean_refunds(refunds):
    refunds["退款日期"] = refunds["退款日期"].apply(parse_date)
    refunds["退款金额"] = refunds["退款金额"].apply(clean_money)
    return refunds


def build_reconciliation_table(orders, payments, refunds):
    refund_summary = refunds.groupby("订单号", as_index=False).agg(
        退款金额=("退款金额", "sum")
    )

    df = orders.merge(
        payments[["订单号", "实收金额", "平台手续费", "支付渠道"]],
        on="订单号",
        how="left",
    )
    df = df.merge(refund_summary, on="订单号", how="left")

    df["实收金额"] = df["实收金额"].fillna(0)
    df["平台手续费"] = df["平台手续费"].fillna(0)
    df["退款金额"] = df["退款金额"].fillna(0)

    df["应收金额"] = df["订单金额"] + df["运费"] - df["退款金额"] - df["平台手续费"]
    df["差异金额"] = df["应收金额"] - df["实收金额"]

    def get_alert_reason(row):
        if row["订单状态"] == "已付款" and row["实收金额"] == 0:
            return "已付款但缺支付流水"
        if row["订单状态"] == "已取消" and row["实收金额"] > 0:
            return "订单取消但存在收款"
        if abs(row["差异金额"]) > 0.01:
            return "金额不一致"
        if row["退款金额"] > 0:
            return "存在退款"
        return "正常"

    df["异常原因"] = df.apply(get_alert_reason, axis=1)
    return df


def build_daily_report(df):
    daily_report = df.groupby(["下单日期", "店铺"], as_index=False).agg(
        GMV=("订单金额", "sum"),
        订单量=("订单号", "count"),
        退款金额=("退款金额", "sum"),
        平台手续费=("平台手续费", "sum"),
        实收金额=("实收金额", "sum"),
    )
    daily_report["净收入"] = daily_report["实收金额"] - daily_report["退款金额"] - daily_report["平台手续费"]
    return daily_report


def main():
    orders, payments, refunds = load_data()

    orders, cleaning_log = clean_orders(orders)
    payments = clean_payments(payments)
    refunds = clean_refunds(refunds)

    clean_orders_df = build_reconciliation_table(orders, payments, refunds)
    daily_report = build_daily_report(clean_orders_df)
    alerts = clean_orders_df[clean_orders_df["异常原因"] != "正常"].copy()

    clean_orders_df.to_csv(OUTPUT_DIR / "clean_orders.csv", index=False, encoding="utf-8-sig")
    daily_report.to_csv(OUTPUT_DIR / "daily_finance_report.csv", index=False, encoding="utf-8-sig")
    alerts.to_csv(OUTPUT_DIR / "reconciliation_alerts.csv", index=False, encoding="utf-8-sig")
    cleaning_log.to_csv(OUTPUT_DIR / "cleaning_log.csv", index=False, encoding="utf-8-sig")

    print("处理完成，已输出：")
    print(OUTPUT_DIR / "clean_orders.csv")
    print(OUTPUT_DIR / "daily_finance_report.csv")
    print(OUTPUT_DIR / "reconciliation_alerts.csv")
    print(OUTPUT_DIR / "cleaning_log.csv")


if __name__ == "__main__":
    main()
