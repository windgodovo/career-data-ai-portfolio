# 运行与实现路线

## 1. MVP 实现顺序

1. 准备样例数据：客户、账户、交易、授信、逾期。
2. 编写 SQL 建模：ODS、DWD、DWS、ADS、SERVING、MONITOR。
3. 输出三类结果：客户分层、异常交易、指标监控。
4. 输出质量报告：主键空值、重复客户、交易金额异常、风险评分范围。
5. 补充图表或 CSV 结果，方便 GitHub 展示和面试讲解。

## 2. 样例数据

当前已准备 5 张 ODS 原始样例表，位置在 `data/ods_raw/`：

| 文件 | 说明 |
|---|---|
| `customer.csv` | 客户基础信息、城市、职业、开户日期、KYC 等级 |
| `account.csv` | 账户信息、余额、状态、账户类型 |
| `transaction.csv` | 交易流水，包含正常消费、转账、夜间大额和失败交易样例 |
| `credit_limit.csv` | 授信额度、已用额度、授信状态 |
| `overdue_record.csv` | 逾期记录、逾期金额、DPD 天数、当前逾期标记 |

快速查看：

```bash
cd "04-bank-risk-customer-analytics"
head -5 data/ods_raw/customer.csv
head -5 data/ods_raw/transaction.csv
```

这些数据里已内置几类可解释的风险样本，例如账户冻结、高额度使用率、当前逾期、夜间连续大额转账、短时间失败交易、向同一外部账户连续转账等。

## 3. 运行脚本

项目已提供两类脚本：

- `scripts/run_pipeline.py`：一键执行 `01_ods.sql` 到 `06_monitor.sql`，并导出结果 CSV。
- `scripts/inspect_sql_results.py`：按步骤查看每层表、上游来源、行数与前 5 行预览。

执行：

```bash
cd "04-bank-risk-customer-analytics"
python3 -m pip install -r requirements.txt
python3 scripts/run_pipeline.py
python3 scripts/inspect_sql_results.py
```

导出结果目录：`data/output/`

- `high_risk_customer_list.csv`
- `customer_segment_result.csv`
- `abnormal_txn_alert_list.csv`
- `data_quality_report.csv`
- `risk_metric_daily_report.csv`

## 4. 推荐技术栈

- 本地演示：DuckDB / PostgreSQL + SQL + Python。
- 扩展计算：PySpark / Spark SQL。
- 实时扩展：Kafka + Spark Structured Streaming。
- 报告展示：CSV / Markdown / 简单 BI Dashboard。

## 5. 验收标准

- 能讲清楚每张核心表来自哪里。
- 能解释客户分层和风险评分口径。
- 能输出异常交易明细及异常原因。
- 能输出指标监控和质量检查结果。
- 能说明如果进入生产环境，Kafka 和 Spark 分别承担什么角色。
