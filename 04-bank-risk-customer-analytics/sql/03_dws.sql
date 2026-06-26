CREATE OR REPLACE TABLE dws.customer_transaction_baseline AS
SELECT
  a.customer_id,
  ROUND(AVG(t.amount), 2) AS avg_amount_30d,
  COALESCE(ROUND(STDDEV_SAMP(t.amount), 2), 0) AS std_amount_30d,
  COUNT(*) AS txn_cnt_30d
FROM dwd.fact_transaction t
JOIN dwd.dim_account a ON t.account_id = a.account_id
WHERE t.txn_time >= (SELECT MAX(txn_time) - INTERVAL 30 DAY FROM dwd.fact_transaction)
GROUP BY a.customer_id;

CREATE OR REPLACE TABLE dws.customer_most_used_channel AS
WITH ch AS (
  SELECT
    a.customer_id,
    t.channel,
    COUNT(*) AS channel_cnt,
    ROW_NUMBER() OVER (PARTITION BY a.customer_id ORDER BY COUNT(*) DESC, t.channel) AS rn
  FROM dwd.fact_transaction t
  JOIN dwd.dim_account a ON t.account_id = a.account_id
  GROUP BY a.customer_id, t.channel
)
SELECT customer_id, channel AS most_used_channel, channel_cnt
FROM ch
WHERE rn = 1;

CREATE OR REPLACE TABLE dws.customer_behavior_30d AS
SELECT
  a.customer_id,
  COUNT(*) AS txn_cnt_30d,
  ROUND(SUM(t.amount), 2) AS txn_amount_30d,
  ROUND(AVG(t.amount), 2) AS avg_txn_amount_30d,
  COUNT(DISTINCT CAST(t.txn_time AS DATE)) AS active_days_30d,
  SUM(CASE WHEN EXTRACT(HOUR FROM t.txn_time) BETWEEN 0 AND 5 THEN 1 ELSE 0 END) AS night_txn_cnt_30d,
  SUM(CASE WHEN t.txn_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_txn_cnt_30d,
  DATE_DIFF('day', MAX(CAST(t.txn_time AS DATE)), (SELECT MAX(CAST(txn_time AS DATE)) FROM dwd.fact_transaction)) AS days_since_last_txn
FROM dwd.fact_transaction t
JOIN dwd.dim_account a ON t.account_id = a.account_id
WHERE t.txn_time >= (SELECT MAX(txn_time) - INTERVAL 30 DAY FROM dwd.fact_transaction)
GROUP BY a.customer_id;

CREATE OR REPLACE TABLE dws.customer_risk_features_30d AS
SELECT
  c.customer_id,
  COALESCE(b.txn_cnt_30d, 0) AS txn_cnt_30d,
  COALESCE(b.txn_amount_30d, 0) AS txn_amount_30d,
  COALESCE(b.night_txn_cnt_30d, 0) AS night_txn_cnt_30d,
  COALESCE(b.failed_txn_cnt_30d, 0) AS failed_txn_cnt_30d,
  COALESCE(cs.utilization_rate, 0) AS credit_utilization_rate,
  COALESCE(ov.overdue_cnt_12m, 0) AS overdue_cnt_12m,
  COALESCE(ov.max_dpd_days_12m, 0) AS max_dpd_days_12m,
  COALESCE(ov.current_overdue_amount, 0) AS current_overdue_amount,
  COALESCE(da.non_active_account_flag, 0) AS non_active_account_flag
FROM dwd.dim_customer c
LEFT JOIN dws.customer_behavior_30d b ON c.customer_id = b.customer_id

LEFT JOIN (
  SELECT customer_id, utilization_rate
  FROM dwd.fact_credit_snapshot
  QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY snapshot_date DESC) = 1
) cs ON c.customer_id = cs.customer_id

LEFT JOIN (
  SELECT
    customer_id,
    COUNT(*) AS overdue_cnt_12m,
    MAX(dpd_days) AS max_dpd_days_12m,
    ROUND(SUM(CASE WHEN is_current_overdue = 1 THEN overdue_amount ELSE 0 END), 2) AS current_overdue_amount
  FROM dwd.fact_overdue_record
  WHERE due_date >= (SELECT MAX(due_date) - INTERVAL 365 DAY FROM dwd.fact_overdue_record)
  GROUP BY customer_id
) ov ON c.customer_id = ov.customer_id

LEFT JOIN (
  SELECT
    customer_id,
    MAX(CASE WHEN status <> 'ACTIVE' THEN 1 ELSE 0 END) AS non_active_account_flag
  FROM dwd.dim_account
  GROUP BY customer_id
) da ON c.customer_id = da.customer_id;

