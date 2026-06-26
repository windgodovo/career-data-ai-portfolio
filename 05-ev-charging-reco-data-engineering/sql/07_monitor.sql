CREATE OR REPLACE TABLE monitor.data_quality_report AS

-- 检查 1：核心事实表不能是空表。
-- 如果 dwd.fact_charge_order 没有任何记录，说明前面的 ODS/DWD 层可能没有正常加载订单数据。
SELECT
  'dwd.fact_charge_order row_count > 0' AS check_item,
  CASE
    WHEN COUNT(*) > 0 THEN 'PASS'
    ELSE 'FAIL'
  END AS check_result,
  CAST(COUNT(*) AS VARCHAR) AS detail
FROM dwd.fact_charge_order

UNION ALL

-- 检查 2：订单事实表的关键字段不能为空。
-- order_id、vehicle_id、station_id 是后续关联维表、支付表和推荐结果的核心键。
SELECT
  'dwd.fact_charge_order key not null' AS check_item,
  CASE
    WHEN SUM(
      CASE
        WHEN order_id IS NULL
          OR vehicle_id IS NULL
          OR station_id IS NULL
        THEN 1
        ELSE 0
      END
    ) = 0 THEN 'PASS'
    ELSE 'FAIL'
  END AS check_result,
  CAST(
    SUM(
      CASE
        WHEN order_id IS NULL
          OR vehicle_id IS NULL
          OR station_id IS NULL
        THEN 1
        ELSE 0
      END
    ) AS VARCHAR
  ) AS detail
FROM dwd.fact_charge_order

UNION ALL

-- 检查 3：最终推荐结果中，每辆车都应该刚好有 3 条推荐。
-- 如果最少推荐数或最多推荐数不是 3，说明 Top-N 排名或候选生成逻辑需要排查。
SELECT
  'serving.charge_reco_topn each vehicle has 3 rows' AS check_item,
  CASE
    WHEN MIN(cnt) = 3 AND MAX(cnt) = 3 THEN 'PASS'
    ELSE 'WARN'
  END AS check_result,
  'min=' || CAST(MIN(cnt) AS VARCHAR)
    || ', max=' || CAST(MAX(cnt) AS VARCHAR) AS detail
FROM (
  SELECT
    vehicle_id,
    COUNT(*) AS cnt
  FROM serving.charge_reco_topn
  GROUP BY vehicle_id
) t;

