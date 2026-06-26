# 数据工程 / BI 数仓方向 CV

## 个人信息

姓名：你的姓名  
邮箱：your.email@example.com  
GitHub：待补充  
LinkedIn：待补充  
目标岗位：数据工程师 / 数据开发 / BI 工程师 / 数据实施

## 个人简介

具备 SQL、Python、DuckDB 和 BI 数据建模能力，能够从原始 CSV / 业务日志出发，设计 ODS、DWD、DWS、ADS、SERVING、MONITOR 分层链路，并输出可运行脚本、数据质量报告和 Dashboard 数据集。

## 核心技能

- SQL：分层建模、宽表构建、窗口函数、质量规则、指标口径。
- Python：Pandas、DuckDB、自动化脚本、CSV 导出、流水线编排。
- 数仓建模：事实表、维度表、指标层、服务层、监控层。
- BI：指标字典、Dashboard 数据集、业务口径沉淀。

## 重点项目

### 新能源汽车充电补能推荐数据工程

项目链接：`05-ev-charging-reco-data-engineering`

- 构建从车辆、充电站、订单、支付、站点运营到推荐结果的完整数据链路。
- 设计 ODS-DWD-DWS-ADS-FEATURE-SERVING-MONITOR 分层 SQL。
- 输出 Top-N 充电站推荐结果、推荐特征宽表和数据质量监控表。
- 使用 DuckDB + Python 实现本地可复现流水线，适合作品集演示和面试讲解。

### 银行风控与客户分析项目

项目链接：`04-bank-risk-customer-analytics`

- 设计客户、账户、交易、授信、逾期等银行数据域。
- 构建 ODS-DWD-DWS-ADS-SERVING-MONITOR 全链路 SQL。
- 输出客户风险评分、异常交易、客户分层、风险指标日报和数据质量报告。
- 使用 inspect 脚本逐层导出中间表 CSV，方便排查和面试展示。

### 金铲铲 DA Dashboard 数据链路

项目链接：`01-golden-spatula-game-da`

- 构建阵容日指标、补丁 delta、玩家迁移和棋子装备风险数据集。
- 使用 ETL 脚本生成 Dashboard 需要的汇总 CSV。

## 面试表达

我做项目时会优先把业务问题拆成数据域和指标口径，再设计 ODS 到 MONITOR 的分层链路。比如 EV 项目里，我从原始订单和站点运营数据出发，构建推荐特征宽表和 Top-N 结果，同时补上质量监控，让项目不只是 SQL 查询，而是完整的数据工程交付。
