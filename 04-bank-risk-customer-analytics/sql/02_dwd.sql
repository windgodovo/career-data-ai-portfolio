CREATE OR REPLACE TABLE dwd.dim_customer AS
SELECT
  customer_id,
  name,
  CAST(age AS INTEGER) AS age,
  city,
  occupation,
  CAST(open_date AS DATE) AS open_date,
  kyc_level
FROM ods.customer;

CREATE OR REPLACE TABLE dwd.dim_account AS
SELECT
  account_id,
  customer_id,
  account_type,
  CAST(balance AS DOUBLE) AS balance,
  UPPER(status) AS status,
  CAST(open_date AS DATE) AS open_date
FROM ods.account;

CREATE OR REPLACE TABLE dwd.fact_transaction AS
SELECT
  txn_id,
  account_id,
  CAST(amount AS DOUBLE) AS amount,
  CAST(txn_time AS TIMESTAMP) AS txn_time,
  LOWER(channel) AS channel,
  LOWER(txn_type) AS txn_type,
  UPPER(txn_status) AS txn_status,
  counterparty_account
FROM ods.transaction;

CREATE OR REPLACE TABLE dwd.fact_credit_snapshot AS
SELECT
  credit_id,
  customer_id,
  CAST(credit_limit AS DOUBLE) AS credit_limit,
  CAST(used_credit AS DOUBLE) AS used_credit,
  CAST(snapshot_date AS DATE) AS snapshot_date,
  UPPER(credit_status) AS credit_status,
  ROUND(CAST(used_credit AS DOUBLE) / NULLIF(CAST(credit_limit AS DOUBLE), 0), 4) AS utilization_rate
FROM ods.credit_limit;

CREATE OR REPLACE TABLE dwd.fact_overdue_record AS
SELECT
  overdue_id,
  customer_id,
  CAST(due_date AS DATE) AS due_date,
  CAST(overdue_amount AS DOUBLE) AS overdue_amount,
  CAST(dpd_days AS INTEGER) AS dpd_days,
  CAST(is_current_overdue AS INTEGER) AS is_current_overdue,
  TRY_CAST(settle_date AS DATE) AS settle_date
FROM ods.overdue_record;
