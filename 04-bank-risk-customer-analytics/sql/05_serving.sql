CREATE OR REPLACE TABLE serving.high_risk_customer_list AS
SELECT
  c.customer_id,
  dc.name,
  dc.city,
  c.risk_score,
  c.risk_level,
  c.credit_utilization_rate,
  c.max_dpd_days_12m,
  c.night_txn_cnt_30d,
  c.failed_txn_cnt_30d
FROM ads.customer_risk_score c
JOIN dwd.dim_customer dc ON c.customer_id = dc.customer_id
WHERE c.risk_level = 'high'
ORDER BY c.risk_score DESC;

CREATE OR REPLACE TABLE serving.customer_segment_result AS
SELECT
  s.customer_id,
  c.name,
  c.city,
  s.customer_segment,
  s.value_score,
  s.active_score,
  s.risk_score,
  s.risk_level
FROM ads.customer_segment s
JOIN dwd.dim_customer c ON s.customer_id = c.customer_id
ORDER BY s.customer_segment, s.risk_score DESC;

CREATE OR REPLACE TABLE serving.abnormal_txn_alert_list AS
SELECT
  a.txn_id,
  a.customer_id,
  c.name,
  c.city,
  a.amount,
  a.txn_time,
  a.channel,
  a.txn_status,
  a.abnormal_reason,
  a.severity
FROM ads.abnormal_transaction_detail a
JOIN dwd.dim_customer c ON a.customer_id = c.customer_id
WHERE a.severity IN ('high', 'medium')
ORDER BY a.severity DESC, a.amount DESC, a.txn_time DESC;
