# 埋点与数据采集设计

## 1. 埋点目标

金铲铲 DA 的埋点目标不是只记录点击，而是还原玩家从进入游戏到完成对局、付费、活动参与和流失的完整链路。

## 2. 核心事件

| 事件 | 含义 | 关键字段 |
|---|---|---|
| `game_login` | 玩家登录 | `player_id`, `server_region`, `platform`, `login_time` |
| `match_start` | 对局开始 | `match_id`, `player_id`, `mode`, `rank_tier`, `patch_version` |
| `round_end` | 回合结束 | `match_id`, `round_no`, `hp_left`, `gold_left`, `level`, `win_flag` |
| `shop_roll` | D 牌行为 | `match_id`, `round_no`, `gold_before`, `gold_after`, `roll_cnt` |
| `level_up` | 升人口 | `match_id`, `round_no`, `level_before`, `level_after`, `gold_cost` |
| `unit_board_state` | 棋子上阵状态 | `match_id`, `round_no`, `unit_id`, `star_level`, `position` |
| `trait_activated` | 羁绊激活 | `match_id`, `round_no`, `trait_id`, `trait_level` |
| `item_equipped` | 装备穿戴 | `match_id`, `unit_id`, `item_id`, `round_no` |
| `match_end` | 对局结束 | `match_id`, `player_id`, `rank_no`, `duration_sec`, `final_comp_id` |
| `payment_success` | 付费成功 | `order_id`, `player_id`, `sku_id`, `amount`, `pay_time` |
| `activity_join` | 活动参与 | `player_id`, `activity_id`, `join_time`, `reward_claimed` |

## 3. 自走棋特有字段

| 字段 | 说明 |
|---|---|
| `patch_version` | 版本/补丁号，所有版本分析必须带上 |
| `season_id` | 赛季 ID，用于赛季级 meta 分析 |
| `mode` | 排位、匹配、娱乐模式、双人模式等 |
| `rank_tier` | 段位，用于区分高低分局 meta |
| `final_comp_id` | 最终阵容 ID，可由棋子/羁绊组合生成 |
| `core_unit_ids` | 核心棋子列表 |
| `trait_combo` | 主要羁绊组合 |
| `item_combo` | 核心装备组合 |
| `econ_path` | 经济运营路径：连胜、连败、快 8、D 牌等 |

## 4. 埋点质量要求

- `match_id`、`player_id`、`patch_version` 必须不能为空。
- 对局开始和结束必须能闭环。
- 回合事件必须按 `round_no` 连续。
- 棋子、羁绊、装备配置必须能关联版本配置表。
- 国内版和海外版字段口径要统一，保留 `region` 区分。
