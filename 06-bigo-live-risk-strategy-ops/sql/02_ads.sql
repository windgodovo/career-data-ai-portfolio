-- 账号级风险特征表：把消息、举报、处罚、设备/IP 关联和支付行为汇总到 user_id 粒度。
CREATE OR REPLACE TABLE ads.risk_account_features AS
WITH msg AS (
  -- 消息特征：统计用户总发言量，以及私信数量。私信高频通常更容易关联诱导、引流和诈骗链路。
  SELECT
    user_id,
    COUNT(DISTINCT message_id) AS message_cnt_all,
    COUNT(DISTINCT CASE WHEN message_type = 'private_message' THEN message_id END) AS private_message_cnt
  FROM ods.message_event
  GROUP BY user_id
), 

report AS (
  -- 举报特征：统计每个被举报用户收到的举报次数。
  SELECT target_id AS user_id, 
  COUNT(DISTINCT report_id) AS report_cnt_all
  FROM ods.report_event
  GROUP BY target_id
), 

punish AS (
  -- 处罚特征：统计每个用户被处罚的次数，用于衡量历史违规强度。
  SELECT user_id, 
  COUNT(DISTINCT punish_id) AS punish_cnt_all
  FROM ods.punishment_event
  GROUP BY user_id
), 

device_cluster AS (
  -- 设备簇特征：同一设备关联的账号越多，越可能存在批量注册或养号行为。
  SELECT a.user_id, 
  COUNT(DISTINCT same_device.user_id) AS device_user_cnt
  FROM ods.account_behavior a
  LEFT JOIN ods.account_behavior same_device
    ON a.device_id = same_device.device_id
  GROUP BY a.user_id
), 

ip_cluster AS (
  -- IP 簇特征：同一 IP 关联多个账号时，可作为团伙或批量操作线索。
  SELECT a.user_id, 
  COUNT(DISTINCT same_ip.user_id) AS ip_user_cnt
  FROM ods.account_behavior a
  LEFT JOIN ods.account_behavior same_ip
    ON a.ip = same_ip.ip
  GROUP BY a.user_id
), 

payment_user AS (
  -- 支付参与用户：付款方和收款方都算作参与该笔支付链路的用户。
  SELECT payer_id AS user_id, order_id, amount FROM ods.payment_order
  UNION
  SELECT receiver_id AS user_id, order_id, amount FROM ods.payment_order
), 

payment AS (
  -- 支付特征：统计用户参与的订单数和金额，用于识别异常礼物流向或诈骗转化链路。
  SELECT
    user_id,
    COUNT(DISTINCT order_id) AS payment_order_cnt,
    ROUND(SUM(amount), 2) AS payment_amount_sum
  FROM payment_user
  GROUP BY user_id
)

SELECT
  a.user_id,
  -- 账号注册时长：用当前 SQL 运行时间减注册时间，值越小越接近“新号”。
  DATE_DIFF('hour', a.register_time, CURRENT_TIMESTAMP) AS account_age_hours,
  COALESCE(msg.message_cnt_all, 0) AS message_cnt_all,
  COALESCE(msg.private_message_cnt, 0) AS private_message_cnt,
  COALESCE(report.report_cnt_all, 0) AS report_cnt_all,
  COALESCE(punish.punish_cnt_all, 0) AS punish_cnt_all,
  COALESCE(device_cluster.device_user_cnt, 0) AS device_user_cnt,
  COALESCE(ip_cluster.ip_user_cnt, 0) AS ip_user_cnt,
  COALESCE(payment.payment_order_cnt, 0) AS payment_order_cnt,
  COALESCE(payment.payment_amount_sum, 0) AS payment_amount_sum
FROM ods.account_behavior a
LEFT JOIN msg ON a.user_id = msg.user_id
LEFT JOIN report ON a.user_id = report.user_id
LEFT JOIN punish ON a.user_id = punish.user_id
LEFT JOIN device_cluster ON a.user_id = device_cluster.user_id
LEFT JOIN ip_cluster ON a.user_id = ip_cluster.user_id
LEFT JOIN payment ON a.user_id = payment.user_id;

-- 房间级风险特征表：从房间维度观察消息、私信、举报和处罚是否集中出现。
CREATE OR REPLACE TABLE ads.risk_room_features AS
SELECT
  r.room_id,
  r.host_id,
  r.room_type,
  r.duration_seconds,
  COUNT(DISTINCT m.message_id) AS message_cnt,
  COUNT(DISTINCT CASE WHEN m.message_type = 'private_message' THEN m.message_id END) AS private_message_cnt,
  COUNT(DISTINCT rep.report_id) AS report_cnt,
  COUNT(DISTINCT p.user_id) AS punished_user_cnt,
  -- 从开播到首条已处罚用户消息的间隔，越短越说明房间可能开场即进入风险行为。
  DATE_DIFF('minute', r.start_time, MIN(CASE WHEN p.punish_id IS NOT NULL THEN m.send_time END)) AS minutes_to_first_punished_message
FROM ods.room_event r
LEFT JOIN ods.message_event m
  ON r.room_id = m.room_id
LEFT JOIN ods.report_event rep
  ON m.user_id = rep.target_id
LEFT JOIN ods.punishment_event p
  ON m.user_id = p.user_id
GROUP BY r.room_id, r.host_id, r.room_type, r.duration_seconds, r.start_time;

-- 话术模板复用表：把数字替换成 <num> 并统一小写，用来识别“数字不同但模板相同”的引流话术。
CREATE OR REPLACE TABLE ads.reused_content_template AS
SELECT
  LOWER(REGEXP_REPLACE(content, '[0-9]+', '<num>', 'g')) AS normalized_content,
  COUNT(DISTINCT user_id) AS sender_cnt,
  COUNT(*) AS message_cnt,
  MIN(send_time) AS first_seen_time,
  MAX(send_time) AS last_seen_time
FROM ods.message_event
GROUP BY normalized_content
HAVING COUNT(DISTINCT user_id) >= 2
   AND COUNT(*) >= 3;

-- 疑似团伙簇表：把设备、IP、支付类别三类关联统一展开，再统计每个簇的举报和处罚情况。
CREATE OR REPLACE TABLE ads.suspect_cluster_result AS
WITH cluster_member AS (
  -- 同设备关系：一个设备对应多个账号，是常见批量注册 / 养号线索。
  SELECT 'device' AS cluster_type, device_id AS cluster_key, user_id
  FROM ods.account_behavior
  UNION ALL
  -- 同 IP 关系：一个 IP 下多个账号，可辅助判断集中操作。
  SELECT 'ip' AS cluster_type, ip AS cluster_key, user_id
  FROM ods.account_behavior
  UNION
  -- 同支付类别关系：付款方和收款方都纳入，用于观察某支付场景下是否集中出现风险用户。
  SELECT 'payment_subject' AS cluster_type, payment_subject AS cluster_key, payer_id AS user_id
  FROM ods.payment_order
  UNION
  SELECT 'payment_subject' AS cluster_type, payment_subject AS cluster_key, receiver_id AS user_id
  FROM ods.payment_order
)
SELECT
  cm.cluster_type,
  cm.cluster_key,
  COUNT(DISTINCT cm.user_id) AS user_cnt,
  COUNT(DISTINCT r.report_id) AS report_cnt,
  COUNT(DISTINCT p.punish_id) AS punish_cnt,
  COUNT(DISTINCT p.user_id) AS punished_user_cnt,
  -- 簇内被处罚用户占比。用被处罚用户数而不是处罚次数，避免单个用户多次处罚把比例放大到超过 1。
  ROUND(
    COUNT(DISTINCT p.user_id) * 1.0 / NULLIF(COUNT(DISTINCT cm.user_id), 0),
    4
  ) AS punish_user_rate
FROM cluster_member cm
LEFT JOIN ods.report_event r
  ON cm.user_id = r.target_id
LEFT JOIN ods.punishment_event p
  ON cm.user_id = p.user_id
GROUP BY cm.cluster_type, cm.cluster_key
-- 只保留至少 2 个用户且至少 1 个用户被处罚的簇，过滤普通单用户行为。
HAVING COUNT(DISTINCT cm.user_id) >= 2
   AND COUNT(DISTINCT p.user_id) >= 1;

-- 行为链特征表：把用户触达房间、私信行为和支付行为串起来，观察“发消息 -> 私信/引流 -> 支付”的链路。
CREATE OR REPLACE TABLE ads.behavior_chain_features AS
WITH msg AS (
  -- 消息链路：统计用户触达过多少房间、发过多少私信，以及首次发言时间。
  SELECT
    user_id,
    COUNT(DISTINCT room_id) AS touched_room_cnt,
    COUNT(DISTINCT CASE WHEN message_type = 'private_message' THEN message_id END) AS private_message_cnt,
    MIN(send_time) AS first_message_time
  FROM ods.message_event
  GROUP BY user_id
), 

payment_user AS (
  -- 支付链路参与方：付款方和收款方都视为该支付链路的一端。
  SELECT payer_id AS user_id, order_id, amount, order_time FROM ods.payment_order
  UNION
  SELECT receiver_id AS user_id, order_id, amount, order_time FROM ods.payment_order
), 

payment AS (
  -- 支付链路汇总：统计参与订单数、金额和首次支付时间。
  SELECT
    user_id,
    COUNT(DISTINCT order_id) AS payment_order_cnt,
    ROUND(SUM(amount), 2) AS payment_amount_sum,
    MIN(order_time) AS first_payment_time
  FROM payment_user
  GROUP BY user_id
)
SELECT
  msg.user_id,
  msg.touched_room_cnt,
  msg.private_message_cnt,
  COALESCE(payment.payment_order_cnt, 0) AS payment_order_cnt,
  COALESCE(payment.payment_amount_sum, 0) AS payment_amount_sum,
  msg.first_message_time,
  payment.first_payment_time
FROM msg
LEFT JOIN payment ON msg.user_id = payment.user_id;

-- 支付类别风险表：按 payment_subject 聚合订单、金额和退款率，识别异常支付类别 / 场景。
CREATE OR REPLACE TABLE ads.payment_flow_risk AS
SELECT
  payment_subject,
  COUNT(DISTINCT payer_id) AS payer_cnt,
  COUNT(DISTINCT receiver_id) AS receiver_cnt,
  COUNT(*) AS order_cnt,
  ROUND(SUM(amount), 2) AS amount_sum,
  ROUND(AVG(refund_flag), 4) AS refund_rate
FROM ods.payment_order
GROUP BY payment_subject
-- 订单数较多或退款率较高的支付类别进入风险观察。
HAVING COUNT(*) >= 2 OR AVG(refund_flag) >= 0.5;

-- 策略候选表：把前面 ADS 层特征转成可执行的策略规则候选，供灰度、复审或限流使用。
CREATE OR REPLACE TABLE serving.risk_strategy_candidate AS
SELECT
  f.user_id,
  -- 按风险命中原因分配策略名称，方便后续策略评审和上线。
  CASE
    WHEN f.device_user_cnt >= 3 AND f.report_cnt_all >= 2 THEN 'device_cluster_review'
    WHEN f.private_message_cnt >= 3 AND f.report_cnt_all >= 1 THEN 'new_account_private_message_limit'
    WHEN f.payment_amount_sum >= 500 AND f.punish_cnt_all >= 1 THEN 'payment_chain_review'
    ELSE 'manual_watchlist'
  END AS strategy_name,
  f.account_age_hours,
  f.private_message_cnt,
  f.report_cnt_all,
  f.punish_cnt_all,
  f.device_user_cnt,
  f.ip_user_cnt,
  f.payment_amount_sum
FROM ads.risk_account_features f
-- 只保留已有举报、处罚、设备聚集或支付金额异常的用户。
WHERE f.report_cnt_all >= 1
   OR f.punish_cnt_all >= 1
   OR f.device_user_cnt >= 3
   OR f.payment_amount_sum >= 500;
