CREATE OR REPLACE TABLE dwd.dim_vehicle AS
SELECT
  vehicle_id,
  user_id,
  home_zone,
  CAST(battery_kwh AS DOUBLE) AS battery_kwh,
  preferred_power_type
FROM ods.vehicle_profile;

CREATE OR REPLACE TABLE dwd.dim_station AS
SELECT
  station_id,
  station_name,
  zone AS station_zone,
  power_type,
  CAST(available_ports AS INTEGER) AS available_ports,
  CAST(tariff_cny_per_kwh AS DOUBLE) AS tariff_cny_per_kwh
FROM ods.charger_station;

CREATE OR REPLACE TABLE dwd.fact_charge_order AS
SELECT
  order_id,
  vehicle_id,
  station_id,
  CAST(start_time AS TIMESTAMP) AS start_time,
  CAST(end_time AS TIMESTAMP) AS end_time,
  CAST(energy_kwh AS DOUBLE) AS energy_kwh,
  status,
  DATE_DIFF('minute', CAST(start_time AS TIMESTAMP), CAST(end_time AS TIMESTAMP)) AS charge_minutes
FROM ods.charge_order
WHERE status = 'COMPLETED';

CREATE OR REPLACE TABLE dwd.fact_payment AS
SELECT
  payment_id,
  order_id,
  CAST(amount_cny AS DOUBLE) AS amount_cny,
  CAST(pay_time AS TIMESTAMP) AS pay_time,
  pay_method,
  CAST(is_success AS INTEGER) AS is_success
FROM ods.payment_txn
WHERE CAST(is_success AS INTEGER) = 1;

CREATE OR REPLACE TABLE dwd.fact_station_ops AS
SELECT
  station_id,
  CAST(snapshot_time AS TIMESTAMP) AS snapshot_time,
  CAST(online_rate AS DOUBLE) AS online_rate,
  CAST(queue_minutes AS INTEGER) AS queue_minutes,
  CAST(fault_count AS INTEGER) AS fault_count
FROM ods.station_ops_snapshot;

