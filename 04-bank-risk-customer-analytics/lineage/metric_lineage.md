# 指标血缘说明

## 1. 客户风险评分 `risk_score`

```text
ods.credit_limit_snapshot
ods.overdue_record
ods.transaction_detail
        ↓
dwd.fact_credit_snapshot
dwd.fact_overdue_record
dwd.fact_transaction
        ↓
dws.customer_risk_features_30d
        ↓
ads.customer_risk_score
        ↓
serving.high_risk_customer_list
```

字段来源：

| ADS 字段 | 上游来源 | 说明 |
|---|---|---|
| `credit_utilization_rate` | `used_credit / credit_limit` | 额度使用率 |
| `overdue_cnt_12m` | `dwd.fact_overdue_record` | 近 12 个月逾期次数 |
| `abnormal_txn_cnt_30d` | `ads.abnormal_transaction_detail` | 近 30 天异常交易次数 |
| `risk_score` | 多字段加权计算 | 综合风险评分 |
| `risk_level` | `risk_score` 分段 | low / medium / high |

## 2. 客户分层 `customer_segment`

```text
ods.customer_profile
ods.account_snapshot
ods.transaction_detail
        ↓
dwd.dim_customer
dwd.dim_account
dwd.fact_transaction
        ↓
dws.customer_behavior_30d
        ↓
ads.customer_segment
        ↓
serving.customer_segment_result
```

字段来源：

| ADS 字段 | 上游来源 | 说明 |
|---|---|---|
| `txn_cnt_30d` | `dwd.fact_transaction` | 近 30 天交易笔数 |
| `txn_amount_30d` | `dwd.fact_transaction` | 近 30 天交易金额 |
| `avg_balance_30d` | `dwd.dim_account` / 快照表 | 平均账户余额 |
| `days_since_last_txn` | `MAX(txn_time)` | 距离最近交易天数 |
| `customer_segment` | value / active / risk 规则 | 客户分层标签 |

## 3. 异常交易 `abnormal_transaction_detail`

```text
ods.transaction_detail
        ↓
dwd.fact_transaction
        ↓
dws.customer_transaction_baseline
        ↓
ads.abnormal_transaction_detail
        ↓
serving.abnormal_txn_alert_list
```

字段来源：

| ADS 字段 | 上游来源 | 说明 |
|---|---|---|
| `txn_id` | `dwd.fact_transaction.txn_id` | 交易编号 |
| `customer_id` | 账户关联客户 | 交易所属客户 |
| `abnormal_reason` | 规则判断 | amount_spike / high_frequency / unusual_channel 等 |
| `severity` | 异常类型和金额综合判断 | low / medium / high |

## 4. 指标监控 `risk_metric_daily_report`

```text
ads.customer_risk_score
ads.customer_segment
ads.abnormal_transaction_detail
monitor.data_quality_report
        ↓
monitor.risk_metric_daily_report
```

监控目标：

- 风险指标是否异常波动。
- 异常交易率是否超过阈值。
- 高风险客户数量是否突然上升。
- 数据质量规则是否有失败项。
