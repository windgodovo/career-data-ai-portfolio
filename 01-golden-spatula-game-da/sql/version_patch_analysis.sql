-- 金铲铲 DA：补丁前后版本分析 SQL 示例

-- 1. 补丁前后阵容变化
WITH before_patch AS (
  SELECT
    final_comp_id,
    COUNT(*) AS play_cnt_before,
    AVG(CASE WHEN rank_no <= 4 THEN 1 ELSE 0 END) AS top4_before,
    AVG(CASE WHEN rank_no = 1 THEN 1 ELSE 0 END) AS win_before
  FROM dwd_match_result
  WHERE patch_version = 'S11.3'
    AND mode = 'ranked'
  GROUP BY final_comp_id
), after_patch AS (
  SELECT
    final_comp_id,
    COUNT(*) AS play_cnt_after,
    AVG(CASE WHEN rank_no <= 4 THEN 1 ELSE 0 END) AS top4_after,
    AVG(CASE WHEN rank_no = 1 THEN 1 ELSE 0 END) AS win_after
  FROM dwd_match_result
  WHERE patch_version = 'S11.4'
    AND mode = 'ranked'
  GROUP BY final_comp_id
)
SELECT
  COALESCE(a.final_comp_id, b.final_comp_id) AS final_comp_id,
  COALESCE(play_cnt_before, 0) AS play_cnt_before,
  COALESCE(play_cnt_after, 0) AS play_cnt_after,
  ROUND(COALESCE(top4_before, 0), 4) AS top4_before,
  ROUND(COALESCE(top4_after, 0), 4) AS top4_after,
  ROUND(COALESCE(top4_after, 0) - COALESCE(top4_before, 0), 4) AS top4_delta,
  ROUND(COALESCE(win_after, 0) - COALESCE(win_before, 0), 4) AS win_delta
FROM before_patch b
FULL OUTER JOIN after_patch a
  ON b.final_comp_id = a.final_comp_id
ORDER BY top4_delta ASC;

-- 2. Meta 迁移：补丁前主玩阵容 -> 补丁后主玩阵容
WITH player_before AS (
  SELECT
    player_id,
    final_comp_id AS comp_before,
    ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY COUNT(*) DESC) AS rn
  FROM dwd_match_result
  WHERE patch_version = 'S11.3'
  GROUP BY player_id, final_comp_id
), player_after AS (
  SELECT
    player_id,
    final_comp_id AS comp_after,
    ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY COUNT(*) DESC) AS rn
  FROM dwd_match_result
  WHERE patch_version = 'S11.4'
  GROUP BY player_id, final_comp_id
)
SELECT
  b.comp_before,
  a.comp_after,
  COUNT(*) AS player_cnt
FROM player_before b
JOIN player_after a ON b.player_id = a.player_id
WHERE b.rn = 1 AND a.rn = 1
GROUP BY b.comp_before, a.comp_after
ORDER BY player_cnt DESC;
