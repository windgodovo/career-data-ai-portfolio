# 银行风控与客户分析架构设计

## 1. 架构目标

本项目的核心不是单纯建表，而是把银行客户与交易数据转化为可用的风控和运营分析结果。架构目标包括：

- 支持客户分层：识别高价值、活跃、沉默、潜在流失客户。
- 支持风控分析：输出客户风险评分和风险等级。
- 支持异常检测：识别大额、高频、渠道异常、时间异常交易。
- 支持指标监控：每日输出风险、交易、客户、质量监控指标。
- 支持数据治理：保留指标口径、质量规则和血缘说明。

## 2. 分层链路

```text
源系统
  ├─ customer_profile
  ├─ account_snapshot
  ├─ transaction_detail
  ├─ credit_limit_snapshot
  └─ overdue_record
        ↓
ODS 原始接入层
        ↓
DWD 标准明细层
        ↓
DWS 汇总服务层
        ↓
ADS 应用指标层
        ↓
SERVING 应用输出层
        ↓
MONITOR 质量与指标监控层
```

## 3. 各层职责

| 层级 | 职责 | 典型产出 |
|---|---|---|
| ODS | 原样接入源系统数据 | `ods.customer_profile`, `ods.transaction_detail` |
| DWD | 字段标准化、类型转换、枚举清洗、主外键校验 | `dwd.dim_customer`, `dwd.fact_transaction` |
| DWS | 按客户、账户、日期聚合行为指标 | `dws.customer_behavior_30d`, `dws.account_risk_30d` |
| ADS | 形成风控和客户分析指标 | `ads.customer_risk_score`, `ads.customer_segment` |
| SERVING | 输出可供业务使用的名单和结果 | `serving.high_risk_customer_list`, `serving.customer_segment_result` |
| MONITOR | 检查数据质量和指标波动 | `monitor.risk_metric_daily_report`, `monitor.data_quality_report` |

## 4. 应用链路

### 4.1 客户分层链路

```text
DWD 客户维表 + DWD 交易事实表 + DWD 账户快照
        ↓
DWS 客户近 30 天交易频次、交易金额、账户余额、最近交易时间
        ↓
ADS 客户价值评分、活跃度评分、风险评分
        ↓
SERVING 客户分层结果
```

### 4.2 风控评分链路

```text
DWD 授信快照 + DWD 逾期记录 + DWD 异常交易标记
        ↓
DWS 客户额度使用率、逾期次数、异常交易次数
        ↓
ADS 客户风险评分
        ↓
SERVING 高风险客户名单
```

### 4.3 异常检测链路

```text
DWD 交易事实表
        ↓
DWS 客户历史交易均值、标准差、常用渠道、常用时段
        ↓
ADS 异常交易规则判断
        ↓
SERVING 异常交易明细与异常原因
```

### 4.4 指标监控链路

```text
ADS 风控指标 + SERVING 风险名单 + MONITOR 质量检查
        ↓
MONITOR 每日指标监控表
        ↓
风险看板 / 质量告警 / 面试展示截图
```

## 5. Spark / Kafka 扩展

本地 demo 可以用 SQL / DuckDB / PostgreSQL 实现。生产环境扩展时：

- Kafka 接入实时交易流水、账户状态变化、授信调整、还款事件。
- Spark Structured Streaming 计算近实时异常交易和滑动窗口风险指标。
- Spark Batch 每日重算客户画像、客户分层和风险评分。
- 指标结果写入数据集市或 API 服务，供风控系统和运营看板使用。
