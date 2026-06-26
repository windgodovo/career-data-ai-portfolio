# 指标口径与业务规则

## 1. 客户分层指标

| 指标 | 口径 | 用途 |
|---|---|---|
| `txn_cnt_30d` | 客户近 30 天交易笔数 | 衡量活跃度 |
| `txn_amount_30d` | 客户近 30 天交易总金额 | 衡量价值贡献 |
| `avg_balance_30d` | 客户近 30 天平均账户余额 | 衡量资金沉淀 |
| `days_since_last_txn` | 距离最近一次交易的天数 | 判断沉默或流失风险 |
| `active_score` | 交易频次和最近交易时间综合评分 | 客户活跃度评分 |
| `value_score` | 余额和交易金额综合评分 | 客户价值评分 |

## 2. 客户分层规则

| 分层 | 判断规则示例 |
|---|---|
| 高价值低风险客户 | `value_score >= 80` 且 `risk_score < 40` |
| 高价值高风险客户 | `value_score >= 80` 且 `risk_score >= 70` |
| 活跃普通客户 | `active_score >= 60` 且 `value_score < 80` 且 `risk_score < 70` |
| 沉默客户 | `days_since_last_txn >= 60` |
| 潜在流失客户 | 历史活跃但近 30 天交易显著下降 |

## 3. 风控指标

| 指标 | 口径 | 说明 |
|---|---|---|
| `credit_utilization_rate` | `used_credit / credit_limit` | 额度使用率 |
| `overdue_cnt_12m` | 近 12 个月逾期次数 | 逾期行为强度 |
| `max_dpd_days_12m` | 近 12 个月最大逾期天数 | 逾期严重程度 |
| `abnormal_txn_cnt_30d` | 近 30 天异常交易笔数 | 异常行为强度 |
| `risk_score` | 多个风险信号加权计算 | 客户综合风险评分 |
| `risk_level` | `low / medium / high` | 风险等级标签 |

## 4. 风险评分示例

```text
risk_score =
  35% * 额度使用压力分
+ 30% * 逾期严重程度分
+ 20% * 异常交易频次分
+ 15% * 账户状态风险分
```

风险等级：

| 等级 | 条件 |
|---|---|
| low | `risk_score < 40` |
| medium | `40 <= risk_score < 70` |
| high | `risk_score >= 70` |

## 5. 异常检测规则

| 规则 | 判断逻辑 | 输出异常原因 |
|---|---|---|
| 大额异常 | 单笔金额 > 客户历史平均金额 × 3 | `amount_spike` |
| 高频异常 | 1 小时内交易笔数 > 10 | `high_frequency` |
| 渠道异常 | 非常用渠道发生大额交易 | `unusual_channel` |
| 夜间异常 | 凌晨发生大额交易 | `night_large_txn` |
| 风险叠加 | 高额度使用率客户出现大额交易 | `risk_stack` |

## 6. 指标监控表

每日输出以下监控指标：

| 指标 | 说明 |
|---|---|
| `total_customer_cnt` | 总客户数 |
| `active_customer_cnt_30d` | 近 30 天活跃客户数 |
| `high_risk_customer_cnt` | 高风险客户数 |
| `abnormal_txn_cnt` | 异常交易笔数 |
| `abnormal_txn_rate` | 异常交易笔数 / 总交易笔数 |
| `overdue_customer_rate` | 当前逾期客户数 / 有授信客户数 |
| `data_quality_pass_rate` | 数据质量规则通过率 |
