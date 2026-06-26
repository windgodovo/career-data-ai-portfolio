# SQL 实现说明

本目录已实现银行风控与客户分析项目的分层 SQL，执行顺序如下：

```text
01_ods.sql       # 原始数据接入（customer/account/transaction/credit/overdue）
02_dwd.sql       # 明细标准化与类型转换
03_dws.sql       # 客户行为、交易基线、风险特征聚合
04_ads.sql       # 客户风险评分、客户分层、异常交易识别
05_serving.sql   # 高风险名单、分层结果、异常告警结果
06_monitor.sql   # 数据质量报告和风险指标监控
```

主要产出表：

- `serving.customer_segment_result`
- `serving.high_risk_customer_list`
- `serving.abnormal_txn_alert_list`

运行方式：

```bash
cd "04-bank-risk-customer-analytics"
python3 scripts/run_pipeline.py
python3 scripts/inspect_sql_results.py
```
