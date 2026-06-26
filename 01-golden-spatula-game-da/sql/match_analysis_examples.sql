-- 金铲铲 DA：对局与阵容分析 SQL 示例

-- 1. 阵容版本表现：出场率、前四率、登顶率、平均名次
WITH comp_perf AS (
  SELECT
    patch_version,
    region,
    rank_tier,
    final_comp_id,
    COUNT(*) AS play_cnt,
    AVG(CASE WHEN rank_no <= 4 THEN 1 ELSE 0 END) AS top4_rate,
    AVG(CASE WHEN rank_no = 1 THEN 1 ELSE 0 END) AS win_rate,
    AVG(rank_no) AS avg_rank
  FROM dwd_match_result
  WHERE mode = 'ranked'
  GROUP BY patch_version, region, rank_tier, final_comp_id
), total AS (
  SELECT
    patch_version,
    region,
    rank_tier,
    SUM(play_cnt) AS total_play_cnt
  FROM comp_perf
  GROUP BY patch_version, region, rank_tier
)
SELECT
  c.patch_version,
  c.region,
  c.rank_tier,
  c.final_comp_id,
  c.play_cnt,
  ROUND(c.play_cnt * 1.0 / t.total_play_cnt, 4) AS pick_rate,
  ROUND(c.top4_rate, 4) AS top4_rate,
  ROUND(c.win_rate, 4) AS win_rate,
  ROUND(c.avg_rank, 2) AS avg_rank
FROM comp_perf c
JOIN total t
  ON c.patch_version = t.patch_version
 AND c.region = t.region
 AND c.rank_tier = t.rank_tier
ORDER BY c.patch_version, pick_rate DESC;

-- 2. 棋子强度：登场率、前四率、装备绑定
SELECT
  patch_version,
  unit_id,
  item_combo,
  COUNT(*) AS appear_cnt,
  ROUND(AVG(CASE WHEN rank_no <= 4 THEN 1 ELSE 0 END), 4) AS top4_rate,
  ROUND(AVG(CASE WHEN rank_no = 1 THEN 1 ELSE 0 END), 4) AS win_rate
FROM dwd_unit_match_detail
GROUP BY patch_version, unit_id, item_combo
HAVING COUNT(*) >= 100
ORDER BY patch_version, top4_rate DESC;

-- 3. 经济节奏：到达 8 人口平均回合
SELECT
  patch_version,
  region,
  rank_tier,
  AVG(first_level8_round) AS avg_level8_round,
  AVG(total_roll_cnt) AS avg_roll_cnt,
  AVG(final_gold) AS avg_final_gold
FROM dws_player_econ_path
GROUP BY patch_version, region, rank_tier
ORDER BY patch_version, region, rank_tier;
