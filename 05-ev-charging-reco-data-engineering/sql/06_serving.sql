CREATE OR REPLACE TABLE serving.charge_reco_topn AS
WITH ranked AS (
  SELECT
    vehicle_id,
    station_id,
    recommend_score,
    ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY recommend_score DESC, station_id) AS rank_no
  FROM feature.vehicle_station_preference_wide
)
SELECT
  vehicle_id,
  station_id,
  recommend_score,
  rank_no
FROM ranked
WHERE rank_no <= 3;
