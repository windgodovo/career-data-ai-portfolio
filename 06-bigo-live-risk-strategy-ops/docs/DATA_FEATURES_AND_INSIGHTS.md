# 数据提取与洞察分析

## 1. 数据源

| 数据源 | 关键字段 | 用途 |
|---|---|---|
| 账号表 | `user_id`, `register_time`, `country`, `device_id`, `ip` | 识别新号、地区、设备簇 |
| 直播/语音房表 | `room_id`, `host_id`, `room_type`, `start_time`, `duration` | 识别房间场景和开播行为 |
| 消息表 | `message_id`, `user_id`, `room_id`, `content`, `send_time` | 识别话术、模板、联系方式 |
| 举报表 | `report_id`, `target_id`, `reason`, `report_time` | 识别用户侧风险反馈 |
| 审核表 | `case_id`, `target_id`, `review_result`, `reviewer` | 评估人审结果和 SOP 一致性 |
| 封禁表 | `punish_id`, `user_id`, `punish_type`, `duration` | 识别处置强度和策略结果 |
| 支付订单表 | `order_id`, `payer_id`, `receiver_id`, `amount`, `payment_subject` | 识别礼物流向、支付类别和诈骗转化 |

## 2. 特征提取方向

### 2.1 账号特征

- 注册时长：`account_age_hours`
- 最近登录国家/地区：`last_country`
- 设备关联账号数：`device_user_cnt_7d`
- IP 关联账号数：`ip_user_cnt_7d`
- 被举报次数：`report_cnt_7d`
- 被处罚次数：`punish_cnt_30d`

### 2.2 行为链特征

- 开播后首次违规消息时间。
- 进入房间后私信次数。
- 同一话术模板复用次数。
- 同一用户触达不同房间数量。
- 直播间观众到私信再到支付的转化链路。

### 2.3 团伙特征

- 同设备多账号。
- 同 IP 多账号。
- 同一支付类别 / 支付场景下出现集中收款、高额支付或高退款。
- 同话术模板。
- 同时间段批量进房或开播。

## 3. 洞察输出模板

不要只输出“数据结果”，要输出结论：

```text
发现：某类新号色情引流风险近 7 天增长 120%。
证据：70% 风险账号注册时间小于 24 小时，集中在 43 个设备簇；其中 58% 使用相似联系方式变体。
策略缺口：现有关键词规则覆盖标准表达，但漏掉昵称、头像和变体文本里的联系方式。
建议：新增设备簇限制 + 新号高频私信阈值 + 变体词表；先在高风险语音房灰度。
预估收益：日均减少 300-500 个风险触达，预计误伤可通过白名单和人工复审控制。
```

## 4. Python 分析方向

- 用 pandas 做 cohort 分析：按注册时间、国家、房间类型聚合风险率。
- 用 networkx 做账号-设备-IP-支付类别-收付款账号关联图。
- 用文本相似度识别话术模板复用。
- 用 z-score / IQR 识别异常处置量、异常举报量和突增房间。
