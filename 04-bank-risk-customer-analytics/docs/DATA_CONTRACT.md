# 数据契约

## 1. 输入表

样例数据位于 `data/ods_raw/`。所有数据均为虚构样例，用于演示客户分层、风险评分、异常交易识别和指标监控。

### customer.csv

| 字段 | 含义 | 类型 |
|---|---|---|
| `customer_id` | 客户 ID | string |
| `name` | 客户姓名 | string |
| `age` | 年龄 | integer |
| `city` | 城市 | string |
| `occupation` | 职业 | string |
| `open_date` | 开户日期 | date |
| `kyc_level` | KYC 等级 | string |

### account.csv

| 字段 | 含义 | 类型 |
|---|---|---|
| `account_id` | 账户 ID | string |
| `customer_id` | 客户 ID | string |
| `account_type` | 账户类型 | string |
| `balance` | 账户余额 | decimal |
| `status` | 账户状态 | string |
| `open_date` | 账户开户日期 | date |

### transaction.csv

| 字段 | 含义 | 类型 |
|---|---|---|
| `txn_id` | 交易 ID | string |
| `account_id` | 账户 ID | string |
| `amount` | 交易金额 | decimal |
| `txn_time` | 交易时间 | timestamp |
| `channel` | 交易渠道 | string |
| `txn_type` | 交易类型 | string |
| `txn_status` | 交易状态 | string |
| `counterparty_account` | 交易对手方账户 | string |

### credit_limit.csv

| 字段 | 含义 | 类型 |
|---|---|---|
| `credit_id` | 授信记录 ID | string |
| `customer_id` | 客户 ID | string |
| `credit_limit` | 授信额度 | decimal |
| `used_credit` | 已用额度 | decimal |
| `snapshot_date` | 快照日期 | date |
| `credit_status` | 授信状态 | string |

### overdue_record.csv

| 字段 | 含义 | 类型 |
|---|---|---|
| `overdue_id` | 逾期记录 ID | string |
| `customer_id` | 客户 ID | string |
| `due_date` | 应还日期 | date |
| `overdue_amount` | 逾期金额 | decimal |
| `dpd_days` | 逾期天数 | integer |
| `is_current_overdue` | 是否当前逾期 | integer |
| `settle_date` | 结清日期 | date |

## 2. 输出表

| 表名 | 说明 |
|---|---|
| `ads_customer_risk_score` | 客户风险评分与风险等级 |
| `ads_customer_segment` | 客户分层标签 |
| `serving_anomaly_transaction` | 异常交易明细 |
| `monitor_metric_alert` | 指标监控告警 |
| `monitor_quality_report` | 数据质量检查结果 |
