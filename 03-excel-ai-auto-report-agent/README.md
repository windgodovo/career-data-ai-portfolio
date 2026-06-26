# Excel AI 自动报表助手项目

这是一个面向运营、财务、电商和中小企业客户的自动化报表作品集项目。项目目标是把每日 Excel / CSV 报表自动转成清洗后的指标表、AI 业务摘要、可发送报告和调度任务，减少人工整理表格的时间和错误。

当前项目已经包含一个 MVP 骨架：支持 CSV / Excel 接入、字段校验、异常行分离、指标计算、AI 摘要生成、结果文件输出和可选邮件发送。

## 1. 项目目标

- 自动读取每日销售或运营报表。
- 对字段、空值、异常值和重复数据做基础校验。
- 计算销售额、订单数、客单价、区域表现、月度趋势等 KPI。
- 使用 LLM 生成业务语言摘要；未配置 API Key 时自动使用本地兜底摘要。
- 输出 CSV、TXT、JSON 等报告产物。
- 支持 SMTP 邮件发送和 cron 定时调度。

## 2. 适用客户

- 运营团队：每日看销售、区域、渠道、异常波动。
- 财务助理：自动整理收入、退款、成本和利润口径。
- 电商商家：自动生成店铺日报、周报、月报。
- Fiverr / Upwork 客户：需要低成本自动化报表交付。

## 3. 运行方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp -n .env.local.example .env.local
python main.py --input data/input/sample_sales.csv --no-email
```

如果没有配置 OpenAI Key，流程会自动使用本地摘要，不影响 MVP 运行。

## 4. 项目结构

```text
03-excel-ai-auto-report-agent/
├── agent/
│   ├── config.py        # 环境变量与配置
│   ├── io_loader.py     # CSV / Excel 读取
│   ├── validate.py      # 字段和数据质量校验
│   ├── metrics.py       # KPI 计算
│   ├── summarizer.py    # AI 摘要与本地兜底摘要
│   ├── report_writer.py # 输出报告文件
│   ├── email_sender.py  # SMTP 邮件发送
│   └── pipeline.py      # 主流程编排
├── data/
│   ├── input/
│   │   └── sample_sales.csv
│   └── output/
├── scheduler/
│   ├── run_daily.sh
│   └── cron.example
├── docs/
│   └── RUNBOOK.md
├── .env.example
├── requirements.txt
├── main.py
└── README.md
```

## 5. 技术架构

```text
Excel / CSV 文件
  ↓
Pandas 读取与字段标准化
  ↓
数据质量校验与异常行分离
  ↓
KPI 指标计算
  ↓
LLM 生成业务摘要 / 本地兜底摘要
  ↓
CSV / TXT / JSON 报告输出
  ↓
邮件发送 / 定时调度
```

可扩展方向：

- PostgreSQL：保存历史指标和报告记录。
- FastAPI：提供上传、触发、查询状态接口。
- Airflow：生产环境任务编排。
- Great Expectations：更系统的数据质量规则。

## 6. 数据治理设计

- ODS：上传的原始 Excel / CSV 快照。
- DWD：按模板清洗后的标准化明细表。
- DWS：日报、周报、月报 KPI 聚合。
- ADS：管理层摘要数据集和邮件 payload。

治理控制：

- 每个模板维护字段字典。
- 对空值、重复值、异常金额进行校验。
- 记录从源文件到最终 KPI 和摘要的处理链路。
- 报告输出中可对个人信息进行脱敏。

## 7. 已实现能力

- CSV / Excel 接入与必填字段校验。
- 数据清洗和异常行分离。
- 按整体、区域、月份计算 KPI。
- OpenAI 摘要生成和本地兜底摘要。
- 输出 CSV、TXT、JSON 文件。
- 可选 SMTP 邮件发送。
- cron 友好的每日调度脚本。

## 8. 交付套餐思路

| 套餐 | 适用场景 | 内容 |
|---|---|---|
| Basic | 单一模板日报 | 一个 Excel 模板、每日摘要邮件、基础 KPI 表 |
| Standard | 多模板运营报表 | 多模板解析、异常检测、周报/月报摘要 |
| Premium | 企业自动化流程 | API 触发、权限分发、客户云环境部署 |

## 9. 验收标准

- 一条命令完成从文件读取到报告输出。
- 报告包含 KPI 表和业务摘要。
- 无效数据进入 validation log，不污染指标。
- 定时任务可连续稳定运行。

## 10. 面试讲法

> 我做了一个 Excel AI 自动报表助手，用 Pandas 完成文件读取、字段校验、数据清洗和 KPI 计算，再用 LLM 生成业务摘要，并支持报告输出、邮件发送和定时调度。这个项目适合展示数据自动化交付能力，也能对应 Fiverr / Upwork 上常见的自动报表需求。