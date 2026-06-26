-- 每日风险指标表：按日期和风险类型统计处罚量，用于观察风险规模和处置结构变化。
CREATE OR REPLACE TABLE monitor.risk_metric_daily AS
SELECT
  CAST(punish_time AS DATE) AS metric_date,
  risk_type,
  COUNT(*) AS punish_cnt,
  COUNT(*) FILTER (WHERE punish_type = 'ban') AS ban_cnt,
  COUNT(*) FILTER (WHERE punish_type = 'mute') AS mute_cnt,
  COUNT(*) FILTER (WHERE punish_type = 'warning') AS warning_cnt
FROM ods.punishment_event
GROUP BY CAST(punish_time AS DATE), risk_type;

-- Bad case 复盘表：把审核记录和账号风险特征合并，给每个 case 自动标注一个初步根因。
CREATE OR REPLACE TABLE monitor.bad_case_review AS
SELECT
  rv.case_id,
  rv.target_id,
  rv.review_time,
  rv.review_result,
  rv.appeal_result,
  COALESCE(f.report_cnt_all, 0) AS report_cnt_all,
  COALESCE(f.private_message_cnt, 0) AS private_message_cnt,
  COALESCE(f.device_user_cnt, 0) AS device_user_cnt,
  COALESCE(f.payment_amount_sum, 0) AS payment_amount_sum,
  -- 根因标签用于复盘分流：误伤、团伙、私信滥用或普通单 case。
  CASE
    WHEN rv.appeal_result = 'overturned' THEN 'possible_false_positive'
    WHEN COALESCE(f.device_user_cnt, 0) >= 3 THEN 'cluster_abuse'
    WHEN COALESCE(f.private_message_cnt, 0) >= 3 THEN 'private_message_abuse'
    ELSE 'single_case_review'
  END AS root_cause
FROM ods.review_event rv
LEFT JOIN ads.risk_account_features f
  ON rv.target_id = f.user_id;

-- 策略效果快照表：汇总当前产出的核心结果规模，作为一次 pipeline 运行后的监控概览。
CREATE OR REPLACE TABLE monitor.strategy_effect_snapshot AS
SELECT
  -- 固定快照日期用于样例数据复现；生产环境可替换为 CURRENT_DATE。
  CAST('2026-06-24' AS DATE) AS snapshot_date,
  (SELECT COUNT(*) FROM ads.risk_account_features) AS account_feature_rows,
  (SELECT COUNT(*) FROM ads.risk_room_features) AS room_feature_rows,
  (SELECT COUNT(*) FROM ads.reused_content_template) AS template_rows,
  (SELECT COUNT(*) FROM ads.suspect_cluster_result) AS suspect_cluster_rows,
  (SELECT COUNT(*) FROM ads.payment_flow_risk) AS risky_payment_subject_rows,
  (SELECT COUNT(*) FROM serving.risk_strategy_candidate) AS strategy_candidate_rows,
  -- 疑似团伙簇的平均处罚用户占比，越高说明簇整体风险越集中。
  ROUND(
    (SELECT AVG(punish_user_rate) FROM ads.suspect_cluster_result),
    4
  ) AS avg_cluster_punish_rate,
  -- 申诉推翻率可作为误杀风险观察指标。
  ROUND(
    (SELECT AVG(CASE WHEN appeal_result = 'overturned' THEN 1 ELSE 0 END) FROM ods.review_event),
    4
  ) AS appeal_overturn_rate;
