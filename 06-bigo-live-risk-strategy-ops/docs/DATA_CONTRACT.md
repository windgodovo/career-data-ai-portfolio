# 数据契约

## 1. 输入数据

### account_behavior

| 字段 | 含义 | 类型 |
|---|---|---|
| `user_id` | 用户 ID | string |
| `register_time` | 注册时间 | timestamp |
| `device_id` | 设备 ID | string |
| `ip` | 登录 IP | string |
| `country` | 国家/地区 | string |
| `is_host` | 是否主播 | integer |

### room_event

| 字段 | 含义 | 类型 |
|---|---|---|
| `room_id` | 房间 ID | string |
| `host_id` | 主播 ID | string |
| `room_type` | 直播 / 语音房类型 | string |
| `start_time` | 开始时间 | timestamp |
| `duration_seconds` | 持续时长 | integer |

### message_event

| 字段 | 含义 | 类型 |
|---|---|---|
| `message_id` | 消息 ID | string |
| `user_id` | 发送人 ID | string |
| `room_id` | 房间 ID | string |
| `content` | 消息内容 | string |
| `send_time` | 发送时间 | timestamp |
| `message_type` | 公屏 / 私信 / 语音转写 | string |

### report_event

| 字段 | 含义 | 类型 |
|---|---|---|
| `report_id` | 举报 ID | string |
| `reporter_id` | 举报人 | string |
| `target_id` | 被举报对象 | string |
| `reason` | 举报原因 | string |
| `report_time` | 举报时间 | timestamp |

### review_event

| 字段 | 含义 | 类型 |
|---|---|---|
| `case_id` | 审核 Case ID | string |
| `target_id` | 被审核对象 | string |
| `review_time` | 审核时间 | timestamp |
| `review_result` | 审核结果 | string |
| `reviewer` | 审核员 | string |
| `appeal_result` | 申诉结果 | string |

### punishment_event

| 字段 | 含义 | 类型 |
|---|---|---|
| `punish_id` | 处罚 ID | string |
| `user_id` | 被处罚用户 | string |
| `punish_type` | 警告 / 禁言 / 下播 / 封禁 | string |
| `risk_type` | 风险类型 | string |
| `punish_time` | 处罚时间 | timestamp |
| `duration_hours` | 处罚时长，警告为 0 | integer |

### payment_order

| 字段 | 含义 | 类型 |
|---|---|---|
| `order_id` | 订单 ID | string |
| `payer_id` | 付款用户 ID | string |
| `receiver_id` | 收款用户 ID | string |
| `amount` | 订单金额 | double |
| `order_time` | 支付时间 | timestamp |
| `payment_subject` | 支付类别标识 / 支付场景标识 | string |
| `refund_flag` | 是否退款 | integer |

## 2. 输出数据

| 表名 | 说明 |
|---|---|
| `ads.risk_account_features` | 账号风险特征 |
| `ads.risk_room_features` | 房间风险特征 |
| `ads.reused_content_template` | 复用话术模板聚合 |
| `ads.suspect_cluster_result` | 疑似团伙簇 |
| `ads.behavior_chain_features` | 用户行为链与支付转化特征 |
| `ads.payment_flow_risk` | 异常支付类别聚合 |
| `serving.risk_strategy_candidate` | 待上线策略候选 |
| `monitor.risk_metric_daily` | 每日风险指标监控 |
| `monitor.bad_case_review` | Bad case 复盘记录 |
| `monitor.strategy_effect_snapshot` | 当前策略效果快照 |
