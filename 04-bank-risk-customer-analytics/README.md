# 银行风控与客户分析项目

这是一个面向银行零售业务的数据分析 / 数据开发作品集项目。项目不再只做抽象的数据治理，而是围绕具体业务应用展开：**客户分层、交易异常检测、风险指标监控、数据质量巡检和监管式数据血缘说明**。

## 1. 项目目标

构建一套银行客户与交易分析链路，从客户、账户、交易、授信、逾期等基础数据出发，形成可解释的风控与运营分析结果：

- 识别高价值客户、活跃客户、沉默客户和潜在流失客户。
- 识别高风险交易、异常金额、异常频次和异常渠道行为。
- 监控客户风险等级、逾期率、交易失败率、异常交易率等核心指标。
- 输出可追踪的数据质量报告和指标血缘，方便面试中解释“数据从哪里来、怎么算、是否可信”。

## 2. 业务场景

银行在零售客户运营和风险控制中，需要同时回答几类问题：

| 场景 | 典型问题 | 项目输出 |
|---|---|---|
| 客户分层 | 哪些客户是高价值客户？哪些客户正在沉默？ | 客户分层标签、客户画像宽表 |
| 风险识别 | 哪些客户有较高逾期或欺诈风险？ | 客户风险评分、风险等级 |
| 异常检测 | 哪些交易金额、频次、渠道行为异常？ | 异常交易明细、异常原因 |
| 指标监控 | 每日风险指标是否波动异常？ | 指标监控表、数据质量报告 |
| 数据治理 | 指标是否有清晰口径和来源？ | 指标口径、血缘映射、质量规则 |

## 3. 数据链路设计

```text
客户信息 / 账户信息 / 交易流水 / 授信记录 / 逾期记录
        ↓
ODS 原始接入层
        ↓
DWD 清洗明细层
        ↓
DWS 客户与账户汇总层
        ↓
ADS 风险与客户分析指标层
        ↓
SERVING 风控名单 / 客户分层结果 / 指标监控结果
        ↓
MONITOR 数据质量与异常巡检
```

## 4. 核心数据域

| 数据域 | 说明 | 示例字段 |
|---|---|---|
| 客户域 | 客户基本信息、地区、年龄、职业、开户时间 | `customer_id`, `age`, `city`, `occupation`, `open_date` |
| 账户域 | 账户状态、余额、账户类型 | `account_id`, `customer_id`, `account_type`, `balance`, `status` |
| 交易域 | 转账、消费、取现、还款等交易流水 | `txn_id`, `account_id`, `amount`, `txn_time`, `channel`, `txn_type` |
| 授信域 | 信用额度、已用额度、额度使用率 | `credit_limit`, `used_credit`, `utilization_rate` |
| 逾期域 | 逾期天数、逾期金额、是否当前逾期 | `dpd_days`, `overdue_amount`, `is_current_overdue` |

样例数据已放在 `data/ods_raw/`，包含客户、账户、交易、授信和逾期 5 类 CSV。项目已补齐可运行的 SQL 分层脚本和 Python 检查脚本，可直接执行 ODS-DWD-DWS-ADS-SERVING-MONITOR 全链路。

## 5. 重点应用环节

### 5.1 风控指标

- 客户风险评分：综合逾期、额度使用率、异常交易次数、账户状态等信号。
- 逾期率：当前逾期客户数 / 有授信客户数。
- 高风险客户数：风险等级为 high 的客户数量。
- 异常交易率：异常交易笔数 / 总交易笔数。
- 额度使用压力：已用额度 / 总授信额度。

### 5.2 客户分层

客户分层不是只按余额排序，而是综合价值、活跃度、风险和稳定性：

| 分层 | 判断思路 |
|---|---|
| 高价值低风险客户 | 余额或交易规模高，风险评分低，逾期记录少 |
| 高价值高风险客户 | 交易规模高，但逾期、额度使用率或异常交易偏高 |
| 活跃普通客户 | 交易频次稳定，余额和风险处于中间区间 |
| 沉默客户 | 最近交易少、账户长期低活跃 |
| 潜在流失客户 | 历史活跃但近期活跃度显著下降 |

### 5.3 异常检测

异常检测采用规则型方法，适合作品集展示和面试解释：

- 单笔金额异常：交易金额超过客户历史均值的若干倍。
- 高频交易异常：短时间内交易次数明显高于客户历史水平。
- 渠道异常：客户突然从非常用渠道发生大额交易。
- 时间异常：非惯常时间段发生高额交易。
- 风险叠加异常：高额度使用率客户同时出现大额或高频交易。

### 5.4 指标监控

每日或每批次输出指标监控表：

- 总客户数、活跃客户数、高风险客户数。
- 总交易金额、交易笔数、异常交易笔数。
- 异常交易率、逾期率、交易失败率。
- 数据质量通过率、关键字段空值数、重复客户数。

## 6. 目录结构

```text
bank-risk-customer-analytics/
├── README.md
├── requirements.txt
├── data/
│   ├── README.md
│   ├── ods_raw/
│   │   ├── account.csv
│   │   ├── credit_limit.csv
│   │   ├── customer.csv
│   │   ├── overdue_record.csv
│   │   └── transaction.csv
│   ├── output/
│   │   ├── abnormal_txn_alert_list.csv
│   │   ├── customer_segment_result.csv
│   │   ├── data_quality_report.csv
│   │   ├── high_risk_customer_list.csv
│   │   └── risk_metric_daily_report.csv
│   └── warehouse/
│       └── bank_risk_customer_analytics.duckdb
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_CONTRACT.md
│   ├── INTERVIEW_TALK.md
│   ├── METRICS_AND_RULES.md
│   └── RUNBOOK.md
├── governance/
│   └── data_governance_policy.yml
├── lineage/
│   ├── README.md
│   └── metric_lineage.md
├── quality-rules/
│   └── risk_quality_rules.yml
├── scripts/
│   ├── inspect_sql_results.py
│   ├── run_pipeline.py
│   └── csv_preview/
│       ├── 01_ods__customer.csv
│       ├── 02_dwd__dim_customer.csv
│       ├── 03_dws__customer_behavior_30d.csv
│       ├── 04_ads__customer_risk_score.csv
│       ├── 05_serving__high_risk_customer_list.csv
│       └── 06_monitor__data_quality_report.csv
├── src/
│   ├── __init__.py
│   └── settings.py
└── sql/
        ├── README.md
        ├── 01_ods.sql
        ├── 02_dwd.sql
        ├── 03_dws.sql
        ├── 04_ads.sql
        ├── 04_ads_example.sql
        ├── 05_abnormal_detection_example.sql
        ├── 05_serving.sql
        └── 06_monitor.sql
```

## 7. 运行方式

一键运行完整链路：

```bash
cd "04-bank-risk-customer-analytics"
python3 -m pip install -r requirements.txt
python3 scripts/run_pipeline.py
```

运行后会生成：

- `data/warehouse/bank_risk_customer_analytics.duckdb`：DuckDB 本地数仓文件。
- `data/output/*.csv`：最终业务结果，包括高风险客户、客户分层、异常交易、质量报告和指标监控。

逐层查看 SQL 运行情况：

```bash
python3 scripts/inspect_sql_results.py
```

这个脚本会按 `01_ods.sql` 到 `06_monitor.sql` 顺序执行，并展示每张表的来源、行数和前 5 行预览。同时，它会把每张中间表完整导出到：

```text
scripts/csv_preview/
```

导出文件使用步骤编号命名，例如：

- `01_ods__customer.csv`
- `02_dwd__fact_transaction.csv`
- `03_dws__customer_risk_features_30d.csv`
- `04_ads__abnormal_transaction_detail.csv`
- `05_serving__customer_segment_result.csv`
- `06_monitor__risk_metric_daily_report.csv`

## 8. Spark / Kafka 扩展方向

当前设计适合用 SQL / DuckDB / PostgreSQL 做本地演示。生产环境可以扩展为：

```text
核心银行系统 / 支付系统 / 风控系统
        ↓
Kafka 交易事件流
        ↓
Spark Structured Streaming 实时计算
        ↓
风险特征表 / 异常交易表 / 指标监控表
        ↓
风控名单、客户运营看板、质量告警
```

- Kafka：接入实时交易、账户状态变更、授信变更、还款事件。
- Spark：计算大规模客户特征、滑动窗口异常指标、每日风险监控报表。
- SQL：继续负责指标口径表达、分层建模和可解释分析。

## 9. 面试讲法

可以这样概括：

> 我把原来的银行数据治理 demo 调整成了一个更贴近业务应用的银行风控与客户分析项目。它从客户、账户、交易、授信和逾期数据出发，设计 ODS-DWD-DWS-ADS-SERVING-MONITOR 链路，输出客户分层、风险评分、异常交易识别和指标监控结果。同时保留数据质量规则和指标血缘，保证分析结果可解释、可追踪、可复核。
