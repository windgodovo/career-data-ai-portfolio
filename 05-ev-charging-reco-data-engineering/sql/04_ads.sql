CREATE OR REPLACE TABLE ads.station_supply_demand_score AS
SELECT
  s.station_id,
  s.station_zone,
  s.available_ports,
  COALESCE(sp.completed_orders_7d, 0) AS completed_orders_7d,
  COALESCE(op.online_rate, 0.0) AS online_rate,
  COALESCE(op.queue_minutes, 0) AS queue_minutes,
  COALESCE(op.fault_count, 0) AS fault_count,
  ROUND(
    0.45 * LEAST(1.0, COALESCE(op.online_rate, 0.0)) +
    0.30 * (1.0 - LEAST(1.0, COALESCE(op.queue_minutes, 0) / 30.0)) +
    0.25 * (1.0 - LEAST(1.0, COALESCE(op.fault_count, 0) / 5.0)),
    4
  ) AS station_operability_score
FROM dwd.dim_station s
LEFT JOIN dws.station_performance_7d sp ON s.station_id = sp.station_id
LEFT JOIN dwd.fact_station_ops op ON s.station_id = op.station_id;




