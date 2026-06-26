CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS ads;
CREATE SCHEMA IF NOT EXISTS serving;
CREATE SCHEMA IF NOT EXISTS monitor;

CREATE OR REPLACE TABLE ods.account_behavior AS
SELECT
  src.user_id,
  CAST(src.register_time AS TIMESTAMP) AS register_time,
  src.device_id,
  src.ip,
  src.country,
  CAST(src.is_host AS INTEGER) AS is_host
FROM read_csv_auto('{{ROOT}}/data/ods_raw/account_behavior.csv', HEADER=TRUE) AS src;

CREATE OR REPLACE TABLE ods.room_event AS
SELECT
  room_id,
  host_id,
  room_type,
  CAST(start_time AS TIMESTAMP) AS start_time,
  CAST(duration_seconds AS INTEGER) AS duration_seconds
FROM read_csv_auto('{{ROOT}}/data/ods_raw/room_event.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.message_event AS
SELECT
  message_id,
  user_id,
  room_id,
  content,
  CAST(send_time AS TIMESTAMP) AS send_time,
  message_type
FROM read_csv_auto('{{ROOT}}/data/ods_raw/message_event.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.report_event AS
SELECT
  report_id,
  target_id,
  CAST(report_time AS TIMESTAMP) AS report_time,
  reason,
  reporter_id
FROM read_csv_auto('{{ROOT}}/data/ods_raw/report_event.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.review_event AS
SELECT
  case_id,
  target_id,
  CAST(review_time AS TIMESTAMP) AS review_time,
  review_result,
  reviewer,
  appeal_result
FROM read_csv_auto('{{ROOT}}/data/ods_raw/review_event.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.punishment_event AS
SELECT
  punish_id,
  user_id,
  CAST(punish_time AS TIMESTAMP) AS punish_time,
  risk_type,
  punish_type,
  CAST(duration_hours AS INTEGER) AS duration_hours
FROM read_csv_auto('{{ROOT}}/data/ods_raw/punishment_event.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.payment_order AS
SELECT
  src.order_id,
  src.payer_id,
  src.receiver_id,
  CAST(src.amount AS DOUBLE) AS amount,
  CAST(src.order_time AS TIMESTAMP) AS order_time,
  src.payment_subject,
  CAST(src.refund_flag AS INTEGER) AS refund_flag
FROM read_csv_auto('{{ROOT}}/data/ods_raw/payment_order.csv', HEADER=TRUE) AS src;
