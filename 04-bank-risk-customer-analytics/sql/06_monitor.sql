CREATE OR REPLACE TABLE monitor.data_quality_report AS
SELECT
  'dwd.dim_customer customer_id not null' AS check_item,
  CASE WHEN SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END AS check_result,
  CAST(SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS VARCHAR) AS detail
FROM dwd.dim_customer

UNION ALL
SELECT
  'dwd.dim_account fk customer_id matched',
  CASE WHEN SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
  CAST(SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS VARCHAR)
FROM dwd.dim_account a
LEFT JOIN dwd.dim_customer c ON a.customer_id = c.customer_id

UNION ALL
SELECT
  'dwd.fact_transaction amount >= 0',
  CASE WHEN SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
  CAST(SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) AS VARCHAR)
FROM dwd.fact_transaction

UNION ALL
SELECT
  'ads.customer_risk_score range 0-100',
  CASE WHEN SUM(CASE WHEN risk_score < 0 OR risk_score > 100 THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
  CAST(SUM(CASE WHEN risk_score < 0 OR risk_score > 100 THEN 1 ELSE 0 END) AS VARCHAR)
FROM ads.customer_risk_score;

CREATE OR REPLACE TABLE monitor.risk_metric_daily_report AS
SELECT
  (SELECT MAX(CAST(txn_time AS DATE)) FROM dwd.fact_transaction) AS metric_date,
  (SELECT COUNT(*) FROM dwd.dim_customer) AS total_customer_cnt,
  (SELECT COUNT(*) FROM dws.customer_behavior_30d WHERE txn_cnt_30d > 0) AS active_customer_cnt_30d,
  (SELECT COUNT(*) FROM ads.customer_risk_score WHERE risk_level = 'high') AS high_risk_customer_cnt,
  (SELECT COUNT(*) FROM ads.abnormal_transaction_detail) AS abnormal_txn_cnt,
  (SELECT COUNT(*) FROM dwd.fact_transaction) AS total_txn_cnt,
  ROUND(
    (SELECT COUNT(*) FROM ads.abnormal_transaction_detail) * 1.0
    / NULLIF((SELECT COUNT(*) FROM dwd.fact_transaction), 0),
    4
  ) AS abnormal_txn_rate,
  ROUND(
    (SELECT COUNT(*) FROM dwd.fact_overdue_record WHERE is_current_overdue = 1) * 1.0
    / NULLIF((SELECT COUNT(*) FROM dwd.fact_credit_snapshot), 0),
    4
  ) AS overdue_customer_rate,
  (SELECT COUNT(*) FROM monitor.data_quality_report WHERE check_result = 'PASS') AS quality_pass_cnt,
  (SELECT COUNT(*) FROM monitor.data_quality_report) AS quality_check_cnt;
