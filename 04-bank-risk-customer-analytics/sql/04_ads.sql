CREATE OR REPLACE TABLE ads.customer_risk_score AS
SELECT
  rf.customer_id,
  rf.credit_utilization_rate,
  rf.overdue_cnt_12m,
  rf.max_dpd_days_12m,
  rf.current_overdue_amount,
  rf.night_txn_cnt_30d,
  rf.failed_txn_cnt_30d,
  ROUND(
    35 * LEAST(rf.credit_utilization_rate, 1)
    + 25 * LEAST(rf.max_dpd_days_12m / 30.0, 1)
    + 20 * LEAST(rf.night_txn_cnt_30d / 5.0, 1)
    + 10 * LEAST(rf.failed_txn_cnt_30d / 3.0, 1)
    + 10 * rf.non_active_account_flag,
    2
  ) AS risk_score,
  CASE
    WHEN ROUND(
      35 * LEAST(rf.credit_utilization_rate, 1)
      + 25 * LEAST(rf.max_dpd_days_12m / 30.0, 1)
      + 20 * LEAST(rf.night_txn_cnt_30d / 5.0, 1)
      + 10 * LEAST(rf.failed_txn_cnt_30d / 3.0, 1)
      + 10 * rf.non_active_account_flag,
      2
    ) >= 70 THEN 'high'
    WHEN ROUND(
      35 * LEAST(rf.credit_utilization_rate, 1)
      + 25 * LEAST(rf.max_dpd_days_12m / 30.0, 1)
      + 20 * LEAST(rf.night_txn_cnt_30d / 5.0, 1)
      + 10 * LEAST(rf.failed_txn_cnt_30d / 3.0, 1)
      + 10 * rf.non_active_account_flag,
      2
    ) >= 40 THEN 'medium'
    ELSE 'low'
  END AS risk_level
FROM dws.customer_risk_features_30d rf;

CREATE OR REPLACE TABLE ads.customer_segment AS
WITH score_base AS (
  SELECT
    c.customer_id,
    COALESCE(b.txn_cnt_30d, 0) AS txn_cnt_30d,
    COALESCE(b.txn_amount_30d, 0) AS txn_amount_30d,
    COALESCE(b.days_since_last_txn, 999) AS days_since_last_txn,
    COALESCE(a.balance, 0) AS balance,
    COALESCE(r.risk_score, 0) AS risk_score,
    COALESCE(r.risk_level, 'low') AS risk_level,
    ROUND(LEAST((COALESCE(b.txn_amount_30d, 0) / 50000.0) * 100, 100), 2) AS value_score,
    ROUND(LEAST((COALESCE(b.txn_cnt_30d, 0) / 20.0) * 100, 100), 2) AS active_score
  FROM dwd.dim_customer c
  LEFT JOIN dws.customer_behavior_30d b ON c.customer_id = b.customer_id
  
  LEFT JOIN (
    SELECT customer_id, SUM(balance) AS balance
    FROM dwd.dim_account
    GROUP BY customer_id
  ) a ON c.customer_id = a.customer_id
  
  LEFT JOIN ads.customer_risk_score r ON c.customer_id = r.customer_id
)
SELECT
  customer_id,
  txn_cnt_30d,
  txn_amount_30d,
  days_since_last_txn,
  balance,
  value_score,
  active_score,
  risk_score,
  risk_level,
  CASE
    WHEN value_score >= 80 AND risk_score < 40 THEN 'high_value_low_risk'
    WHEN value_score >= 80 AND risk_score >= 70 THEN 'high_value_high_risk'
    WHEN days_since_last_txn >= 30 THEN 'silent_customer'
    WHEN active_score >= 40 AND risk_score < 70 THEN 'active_normal_customer'
    ELSE 'general_customer'
  END AS customer_segment
FROM score_base;

CREATE OR REPLACE TABLE ads.abnormal_transaction_detail AS
WITH t_enriched AS (
  SELECT
    t.txn_id,
    a.customer_id,
    t.account_id,
    t.amount,
    t.txn_time,
    t.channel,
    t.txn_type,
    t.txn_status,
    COALESCE(b.avg_amount_30d, t.amount) AS avg_amount_30d,
    COALESCE(b.txn_cnt_30d, 1) AS txn_cnt_30d,
    COALESCE(m.most_used_channel, t.channel) AS most_used_channel,
    COUNT(*) OVER (
      PARTITION BY a.customer_id, DATE_TRUNC('hour', t.txn_time)
    ) AS hourly_txn_cnt
  FROM dwd.fact_transaction t
  JOIN dwd.dim_account a ON t.account_id = a.account_id
  LEFT JOIN dws.customer_transaction_baseline b ON a.customer_id = b.customer_id
  LEFT JOIN dws.customer_most_used_channel m ON a.customer_id = m.customer_id
)
SELECT
  txn_id,
  customer_id,
  account_id,
  amount,
  txn_time,
  channel,
  txn_type,
  txn_status,
  CASE
    WHEN amount > avg_amount_30d * 3 THEN 'amount_spike'
    WHEN hourly_txn_cnt >= 3 THEN 'high_frequency'
    WHEN EXTRACT(HOUR FROM txn_time) BETWEEN 0 AND 5 AND amount > avg_amount_30d * 2 THEN 'night_large_txn'
    WHEN channel <> most_used_channel AND amount > avg_amount_30d * 1.5 THEN 'unusual_channel'
    WHEN txn_status = 'FAILED' AND amount > avg_amount_30d THEN 'failed_large_txn'
    ELSE 'normal'
  END AS abnormal_reason,
  
  CASE
    WHEN amount > avg_amount_30d * 3 OR hourly_txn_cnt >= 4 THEN 'high'
    WHEN amount > avg_amount_30d * 2 OR hourly_txn_cnt >= 3 THEN 'medium'
    ELSE 'low'
  END AS severity
FROM t_enriched
WHERE amount > avg_amount_30d * 2
   OR hourly_txn_cnt >= 3
   OR (EXTRACT(HOUR FROM txn_time) BETWEEN 0 AND 5 AND amount > avg_amount_30d * 1.5)
   OR (channel <> most_used_channel AND amount > avg_amount_30d * 1.5)
   OR (txn_status = 'FAILED' AND amount > avg_amount_30d);
