CREATE OR REPLACE TABLE feature.vehicle_station_preference_wide AS
WITH vehicle_station_base AS (
  SELECT
    v.vehicle_id,
    s.station_id,
    CASE WHEN v.home_zone = s.station_zone THEN 1 ELSE 0 END AS zone_match,
    CASE WHEN v.preferred_power_type = s.power_type THEN 1 ELSE 0 END AS power_match,
    s.tariff_cny_per_kwh,
    a.station_operability_score,
    COALESCE(p.session_cnt_30d, 0) AS session_cnt_30d,
    COALESCE(p.avg_energy_kwh_30d, 0) AS avg_energy_kwh_30d,
    COALESCE(p.avg_amount_cny_30d, 0) AS avg_amount_cny_30d
  FROM dwd.dim_vehicle v
  CROSS JOIN dwd.dim_station s
  LEFT JOIN dws.vehicle_station_preference_30d p
    ON v.vehicle_id = p.vehicle_id AND s.station_id = p.station_id
  LEFT JOIN ads.station_supply_demand_score a
    ON s.station_id = a.station_id
)
SELECT
  vehicle_id,
  station_id,
  zone_match,
  power_match,
  tariff_cny_per_kwh,
  station_operability_score,
  session_cnt_30d,
  avg_energy_kwh_30d,
  avg_amount_cny_30d,
  ROUND(
    0.35 * LEAST(1.0, session_cnt_30d / 4.0) +
    0.25 * zone_match +
    0.15 * power_match +
    0.15 * station_operability_score +
    0.10 * (1.0 - LEAST(1.0, tariff_cny_per_kwh / 2.2)),
    4
  ) AS recommend_score
FROM vehicle_station_base;
