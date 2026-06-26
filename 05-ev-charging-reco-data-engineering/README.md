# 新能源汽车充电补能推荐数据工程项目

这是一个面向**汽车 / 新能源充电补能场景**的数据工程作品集项目。项目模拟从车辆、充电站、充电订单、支付流水和站点运营数据出发，完成数据接入、清洗建模、特征宽表、推荐结果输出和数据质量监控的完整链路。

英文版 README 已移至 [docs/README_EN.md](docs/README_EN.md)。

## 项目定位

本项目适合用于投递以下方向：

- 数据工程师 / 数据开发助理
- 汽车行业数据分析
- 新能源充电运营分析
- BI / 数仓 / 数据实施岗位
- 产业数字化转型相关岗位

它重点展示的不是单个算法模型，而是一个业务数据项目从原始数据到可服务结果的工程化过程。

## 业务背景

在新能源汽车补能场景中，用户选择充电站时通常会受到以下因素影响：

- 站点距离或区域是否方便
- 充电站可用端口是否充足
- 排队时间是否过长
- 电价是否有竞争力
- 用户历史上是否偏好该站点或同类站点
- 站点运营状态是否稳定

本项目通过模拟数据构建一个简化版充电推荐链路，为每辆车输出 Top-N 推荐充电站。

## 数据链路

```text
车辆 / 充电站 / 充电订单 / 支付 / 站点运营
	↓
ODS 原始接入
	↓
DWD 清洗标准化
	↓
DWS 聚合指标层
	↓
ADS 业务指标层
	↓
FEATURE 推荐特征宽表
	↓
SERVING Top-N 推荐结果
	↓
MONITOR 数据质量监控
```

## 项目结构

```text
05-ev-charging-reco-data-engineering/
├── data/
│   ├── ods_raw/        # 原始 CSV 样例数据
│   ├── output/         # 推荐结果、特征宽表、质量报告
│   └── warehouse/      # DuckDB 本地数仓文件
├── docs/
│   ├── ARCHITECTURE.md # 架构说明
│   ├── DATA_CONTRACT.md# 数据契约
│   ├── README_EN.md    # 英文版 README
│   ├── architecture_pipeline.drawio
│   └── star_schema_er.drawio
├── scripts/
│   └── run_pipeline.py # 一键运行流水线
├── sql/
│   ├── 01_ods.sql
│   ├── 02_dwd.sql
│   ├── 03_dws.sql
│   ├── 04_ads.sql
│   ├── 05_features.sql
│   ├── 06_serving.sql
│   └── 07_monitor.sql
├── src/
│   └── settings.py     # 路径与运行配置
├── requirements.txt
└── README.md
```

## 输入数据

原始数据位于 `data/ods_raw/`：

| 文件 | 含义 |
|---|---|
| `vehicle_profile.csv` | 车辆与用户基础信息 |
| `charger_station.csv` | 充电站基础信息、区域、功率、电价 |
| `charge_order.csv` | 充电订单明细 |
| `payment_txn.csv` | 支付流水 |
| `station_ops_snapshot.csv` | 站点运营快照，如在线率、排队时间、故障数 |

## 输出结果

运行后会在 `data/output/` 生成：

| 文件 | 含义 |
|---|---|
| `charge_reco_topn.csv` | 每辆车的 Top-N 推荐充电站 |
| `vehicle_station_preference_wide.csv` | 车辆-站点级推荐特征宽表 |
| `data_quality_report.csv` | 数据质量检查结果 |

## 快速开始

```bash
cd "05-ev-charging-reco-data-engineering"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
```

运行成功后，终端会输出 SQL 分层任务执行日志，并展示推荐结果预览。

## 最快查看 SQL 运行结果和数据来源

如果你想一边看每个 SQL 文件的结果，一边看每张表来自哪里，运行：

```bash
python scripts/inspect_sql_results.py
```

这个脚本会按顺序执行：

```text
01_ods.sql -> 02_dwd.sql -> 03_dws.sql -> 04_ads.sql -> 05_features.sql -> 06_serving.sql -> 07_monitor.sql
```

每一步都会打印：

- 当前执行的 SQL 文件
- 这一层产出的数据表
- 数据表的上游来源
- 表行数
- 前 5 行预览结果

例如你正在看 `sql/03_dws.sql`，可以直接运行 `inspect_sql_results.py`，然后找到：

```text
Step 3: 03_dws.sql
Table: dws.station_performance_7d
Source: dwd.fact_charge_order + dwd.fact_payment
```

这样就能快速知道：这条 SQL 的结果表是什么，以及它的数据来自哪些上游表。

## 推荐逻辑说明

本 demo 的推荐分数综合考虑：

- 用户历史充电偏好
- 车辆所在区域与站点区域是否匹配
- 站点排队压力
- 站点可用端口数量
- 电价竞争力
- 站点运营稳定性

最终输出每辆车推荐分数最高的充电站，并按照 `rank_no` 排序。

## 技术栈

- Python
- DuckDB
- Pandas
- SQL 分层建模
- CSV 本地数据源
- ODS / DWD / DWS / ADS / FEATURE / SERVING / MONITOR 分层思想

## Spark / Kafka 生产化扩展架构

当前版本使用 CSV + DuckDB，重点是让作品集项目可以在本地快速运行和讲解。如果进入真实企业场景，可以扩展为 Kafka + Spark 架构：

```text
App / 充电桩 / 支付系统 / 站点运营系统
	↓
Kafka Topics 实时事件流
	↓
Spark Structured Streaming / Spark Batch
	↓
ODS / DWD / DWS / ADS / FEATURE
	↓
推荐结果 Serving + Monitor 数据质量监控
```

- **Kafka**：承接充电订单、支付流水、站点状态、车辆画像变更等实时事件，替代手工 CSV 接入。
- **Spark Structured Streaming**：实时维护站点在线率、排队时间、故障数、最近 7 天站点表现、最近 30 天车辆偏好等滑动窗口指标。
- **Spark Batch**：适合每天或每小时重算大规模车辆-站点候选集、特征宽表和 Top-N 推荐结果。
- **数据湖格式**：可进一步接入 Parquet / Delta Lake / Iceberg，支持增量计算、历史回溯和数据版本管理。

这个扩展方向可以把本地 demo 升级为更接近生产环境的“批流一体”数据工程方案。

## 项目亮点

- **业务场景清晰**：围绕新能源汽车充电补能推荐，不是孤立 SQL 练习。
- **数仓分层完整**：从 ODS 到 Serving 和 Monitor，结构接近真实数据工程链路。
- **可一键运行**：通过 `scripts/run_pipeline.py` 完成建库、执行 SQL、导出结果。
- **结果可检查**：输出推荐结果、特征宽表和数据质量报告。
- **图文配套**：提供 DWD ER 图和数据架构 Pipeline 图，方便解释表关系和任务链路。
- **适合面试讲解**：可以从业务目标、数据契约、分层建模、指标口径和推荐策略逐层展开。

## 架构图

- [docs/star_schema_er.drawio](docs/star_schema_er.drawio)：DWD 层 ER 图，展示维表、事实表和关键关联字段。
- [docs/architecture_pipeline.drawio](docs/architecture_pipeline.drawio)：数据架构 Pipeline 图，展示从 ODS 到 MONITOR 的完整链路。

## 适合怎么讲给面试官

可以用下面这段话概括：

> 我做了一个新能源汽车充电推荐方向的数据工程 demo。项目从车辆、站点、订单、支付和运营快照等原始数据出发，用 DuckDB 和 SQL 搭建 ODS、DWD、DWS、ADS、FEATURE、SERVING、MONITOR 分层链路，最终为每辆车输出 Top-N 推荐充电站，并生成数据质量报告。这个项目主要展示我对业务指标、数仓分层、特征宽表和可复现数据流水线的理解。

## 后续可扩展方向

- 接入真实地图距离或经纬度数据
- 增加时段峰谷电价特征
- 增加用户充电时间偏好
- 将推荐规则升级为可训练模型
- 使用 Airflow / Dagster 编排 SQL 任务
- 接入 BI 看板展示站点利用率和推荐效果
