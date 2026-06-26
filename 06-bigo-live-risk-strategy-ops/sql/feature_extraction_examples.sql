-- BIGO LIVE 直播风控策略运营：特征提取 SQL 示例
-- 这些 SQL 是作品集级示例，用于表达如何从账号、房间、消息、举报、审核、处罚和支付行为中抽取风险信号。

-- 1. 新号高频互动 + 举报特征
CREATE OR REPLACE TABLE ads.risk_account_features AS
WITH msg AS (
  SELECT
    user_id,
    COUNT(DISTINCT message_id) AS message_cnt_24h,
    COUNT(DISTINCT CASE WHEN message_type = 'private_message' THEN message_id END) AS private_message_cnt_24h
  FROM ods.message_event
  WHERE send_time >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
  GROUP BY user_id
), report AS (
  SELECT target_id AS user_id, COUNT(DISTINCT report_id) AS report_cnt_7d
  FROM ods.report_event
  WHERE report_time >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
  GROUP BY target_id
), punish AS (
  SELECT user_id, COUNT(DISTINCT punish_id) AS punish_cnt_30d
  FROM ods.punishment_event
  WHERE punish_time >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
  GROUP BY user_id
), payment_user AS (
  SELECT payer_id AS user_id, order_id, amount FROM ods.payment_order
  UNION
  SELECT receiver_id AS user_id, order_id, amount FROM ods.payment_order
), payment AS (
  SELECT user_id, COUNT(DISTINCT order_id) AS payment_order_cnt, SUM(amount) AS payment_amount_sum
  FROM payment_user
  GROUP BY user_id
), device_cluster AS (
  SELECT a.user_id, COUNT(DISTINCT same_device.user_id) AS device_user_cnt_7d
  FROM ods.account_behavior a
  LEFT JOIN ods.account_behavior same_device
    ON a.device_id = same_device.device_id
    AND same_device.register_time >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
  GROUP BY a.user_id
), ip_cluster AS (
  SELECT a.user_id, COUNT(DISTINCT same_ip.user_id) AS ip_user_cnt_7d
  FROM ods.account_behavior a
  LEFT JOIN ods.account_behavior same_ip
    ON a.ip = same_ip.ip
    AND same_ip.register_time >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
  GROUP BY a.user_id
)
SELECT
  a.user_id,
  DATE_DIFF('hour', a.register_time, CURRENT_TIMESTAMP) AS account_age_hours,
  COALESCE(msg.message_cnt_24h, 0) AS message_cnt_24h,
  COALESCE(msg.private_message_cnt_24h, 0) AS private_message_cnt_24h,
  COALESCE(report.report_cnt_7d, 0) AS report_cnt_7d,
  COALESCE(punish.punish_cnt_30d, 0) AS punish_cnt_30d,
  COALESCE(device_cluster.device_user_cnt_7d, 0) AS device_user_cnt_7d,
  COALESCE(ip_cluster.ip_user_cnt_7d, 0) AS ip_user_cnt_7d,
  COALESCE(payment.payment_order_cnt, 0) AS payment_order_cnt,
  COALESCE(payment.payment_amount_sum, 0) AS payment_amount_sum
FROM ods.account_behavior a
LEFT JOIN msg ON a.user_id = msg.user_id
LEFT JOIN report ON a.user_id = report.user_id
LEFT JOIN punish ON a.user_id = punish.user_id
LEFT JOIN payment ON a.user_id = payment.user_id
LEFT JOIN device_cluster ON a.user_id = device_cluster.user_id
LEFT JOIN ip_cluster ON a.user_id = ip_cluster.user_id;

-- 2. 房间风险特征：房间消息、私信、举报和处罚聚合
CREATE OR REPLACE TABLE ads.risk_room_features AS
SELECT
  r.room_id,
  r.host_id,
  r.room_type,
  r.duration_seconds,
  COUNT(DISTINCT m.message_id) AS message_cnt,
  COUNT(DISTINCT CASE WHEN m.message_type = 'private_message' THEN m.message_id END) AS private_message_cnt,
  COUNT(DISTINCT rep.report_id) AS report_cnt,
  COUNT(DISTINCT p.user_id) AS punished_user_cnt
FROM ods.room_event r
LEFT JOIN ods.message_event m ON r.room_id = m.room_id
LEFT JOIN ods.report_event rep ON m.user_id = rep.target_id
LEFT JOIN ods.punishment_event p ON m.user_id = p.user_id
GROUP BY r.room_id, r.host_id, r.room_type, r.duration_seconds;

-- 3. 内容模板复用：同一标准化文本被多个账号重复发送
CREATE OR REPLACE TABLE ads.reused_content_template AS
SELECT
  LOWER(REGEXP_REPLACE(content, '[0-9]+', '<num>', 'g')) AS normalized_content,
  COUNT(DISTINCT user_id) AS sender_cnt,
  COUNT(*) AS message_cnt,
  MIN(send_time) AS first_seen_time,
  MAX(send_time) AS last_seen_time
FROM ods.message_event
WHERE send_time >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
GROUP BY normalized_content
HAVING COUNT(DISTINCT user_id) >= 5
   AND COUNT(*) >= 20;

-- 4. 疑似团伙簇：同设备 / 同 IP / 同支付类别标识聚合
CREATE OR REPLACE TABLE ads.suspect_cluster_result AS
WITH cluster_member AS (
  SELECT 'device' AS cluster_type, device_id AS cluster_key, user_id FROM ods.account_behavior
  UNION ALL
  SELECT 'ip' AS cluster_type, ip AS cluster_key, user_id FROM ods.account_behavior
  UNION
  SELECT 'payment_subject' AS cluster_type, payment_subject AS cluster_key, payer_id AS user_id FROM ods.payment_order
  UNION
  SELECT 'payment_subject' AS cluster_type, payment_subject AS cluster_key, receiver_id AS user_id FROM ods.payment_order
)
SELECT
  cm.cluster_type,
  cm.cluster_key,
  COUNT(DISTINCT cm.user_id) AS user_cnt,
  COUNT(DISTINCT r.report_id) AS report_cnt,
  COUNT(DISTINCT p.punish_id) AS punish_cnt,
  COUNT(DISTINCT p.user_id) AS punished_user_cnt,
  ROUND(
    COUNT(DISTINCT p.user_id) * 1.0 / NULLIF(COUNT(DISTINCT cm.user_id), 0),
    4
  ) AS punish_user_rate
FROM cluster_member cm
LEFT JOIN ods.report_event r ON cm.user_id = r.target_id
LEFT JOIN ods.punishment_event p ON cm.user_id = p.user_id
GROUP BY cm.cluster_type, cm.cluster_key
HAVING COUNT(DISTINCT cm.user_id) >= 3
   AND COUNT(DISTINCT p.user_id) >= 1;

-- 5. 待上线策略候选：把高风险特征转成规则候选
CREATE OR REPLACE TABLE serving.risk_strategy_candidate AS
SELECT
  user_id,
  CASE
    WHEN device_user_cnt_7d >= 3 AND report_cnt_7d >= 2 THEN 'device_cluster_review'
    WHEN private_message_cnt_24h >= 3 AND report_cnt_7d >= 1 THEN 'new_account_private_message_limit'
    WHEN payment_amount_sum >= 500 AND punish_cnt_30d >= 1 THEN 'payment_chain_review'
    ELSE 'manual_watchlist'
  END AS strategy_name
FROM ads.risk_account_features
WHERE report_cnt_7d >= 1
   OR punish_cnt_30d >= 1
   OR device_user_cnt_7d >= 3
   OR payment_amount_sum >= 500;

-- 6. 每日风险指标监控
CREATE OR REPLACE TABLE monitor.risk_metric_daily AS
SELECT
  CAST(punish_time AS DATE) AS metric_date,
  risk_type,
  COUNT(*) AS punish_cnt,
  COUNT(*) FILTER (WHERE punish_type = 'ban') AS ban_cnt,
  COUNT(*) FILTER (WHERE punish_type = 'mute') AS mute_cnt,
  COUNT(*) FILTER (WHERE punish_type = 'warning') AS warning_cnt
FROM ods.punishment_event
GROUP BY CAST(punish_time AS DATE), risk_type;
