-- 7-day aggregation by station
CREATE OR REPLACE TABLE dws.station_performance_7d AS
SELECT
  o.station_id,
  COUNT(*) AS completed_orders_7d,
  ROUND(AVG(o.energy_kwh), 2) AS avg_energy_kwh_7d,
  ROUND(AVG(o.charge_minutes), 2) AS avg_charge_minutes_7d,
  ROUND(SUM(p.amount_cny), 2) AS total_revenue_cny_7d
FROM dwd.fact_charge_order o
LEFT JOIN dwd.fact_payment p ON o.order_id = p.order_id
WHERE o.start_time >= (SELECT MAX(start_time) - INTERVAL 7 DAY FROM dwd.fact_charge_order)
GROUP BY o.station_id;

-- 30-day aggregation by vehicle-station pair
CREATE OR REPLACE TABLE dws.vehicle_station_preference_30d AS
SELECT
  o.vehicle_id,
  o.station_id,
  COUNT(*) AS session_cnt_30d,
  ROUND(AVG(o.energy_kwh), 2) AS avg_energy_kwh_30d,
  ROUND(AVG(COALESCE(p.amount_cny, 0)), 2) AS avg_amount_cny_30d
FROM dwd.fact_charge_order o
LEFT JOIN dwd.fact_payment p ON o.order_id = p.order_id
WHERE o.start_time >= (SELECT MAX(start_time) - INTERVAL 30 DAY FROM dwd.fact_charge_order)
GROUP BY o.vehicle_id, o.station_id;
