# 义乌电商订单财务对账与日报自动化

这是一个面向**义乌财务数据岗位 / 电商订单对账岗位**的实操练习项目。

项目模拟义乌电商公司每日处理订单、支付流水、退款数据的真实场景，完成：

- 原始订单数据清洗
- 金额、日期、文本字段标准化
- 订单与支付流水对账
- 退款金额统计
- 财务日报汇总
- 对账异常输出
- 清洗日志记录
- Pandas 自动化脚本复现

项目重点不是做复杂模型，而是训练财务数据岗位最看重的三件事：

1. **数据准确**
2. **过程可追溯**
3. **异常能定位**

---

## 项目结构

```text
projects/yiwu-finance-data-interview-project/
├── README.md
├── requirements.txt
├── create_yiwu_finance_project.py
├── finance_reconciliation_demo.py
├── data/
│   ├── raw/
│   │   ├── order_raw.csv
│   │   ├── pay_raw.csv
│   │   └── refund_raw.csv
│   └── output/
│       ├── clean_orders.csv
│       ├── daily_finance_report.csv
│       ├── reconciliation_alerts.csv
│       └── cleaning_log.csv
└── docs/
    ├── Excel实操练习说明.md
    ├── Pandas自动化说明.md
    └── 面试话术.md
```

---

## 数据说明

### 1. 订单原始表：`data/raw/order_raw.csv`

包含以下脏数据：

- 空行
- 重复订单
- 日期格式不统一：`2025/1/1`、`2025-01-01`、`20250102`
- 金额带 `¥` 和逗号：`¥1,200`
- 省份错别字：`浙冮`、`廣东`
- 文本字段带空格

### 2. 支付流水表：`data/raw/pay_raw.csv`

用于和订单表按 `订单号` 对账，包含实收金额、平台手续费和支付渠道。

### 3. 退款表：`data/raw/refund_raw.csv`

用于统计订单退款金额，并参与应收金额计算。

---

## 输出结果

运行脚本后会生成以下结果：

| 文件 | 说明 |
|---|---|
| `clean_orders.csv` | 清洗后的订单明细 |
| `daily_finance_report.csv` | 按日期和店铺汇总的财务日报 |
| `reconciliation_alerts.csv` | 对账异常订单明细 |
| `cleaning_log.csv` | 清洗过程日志 |

---

## 快速运行

进入项目目录：

```bash
cd projects/yiwu-finance-data-interview-project
```

安装依赖：

```bash
pip install -r requirements.txt
```

运行自动化脚本：

```bash
python finance_reconciliation_demo.py
```

如需生成 Excel 练习文件和压缩包，可以运行：

```bash
python create_yiwu_finance_project.py
```

---

## Excel 实操训练重点

这个项目可用于面试前练习：

- 删除空行、重复行
- 统一日期格式
- 清洗金额字段中的 `¥` 和逗号
- 使用 `TRIM` / `CLEAN` / `SUBSTITUTE` 处理文本
- 使用 `XLOOKUP` 匹配支付流水
- 使用 `SUMIFS` / `COUNTIFS` 做多条件汇总
- 使用 `IF` 判断对账异常
- 使用透视表生成日报
- 保留原始数据，单独输出清洗表、汇总表、异常表和日志表

---

## 面试项目介绍

可以这样介绍本项目：

> 我准备了一个义乌电商订单财务对账项目，模拟订单、支付流水和退款三张表。  
> 我先用 Excel 处理重复行、日期格式、金额格式、省份错别字等问题，然后用 XLOOKUP、SUMIFS、COUNTIFS、IF 和透视表完成日报汇总和订单对账。  
> 同时，我也用 Pandas 写了自动化脚本，可以自动输出财务日报、异常明细表和清洗日志。  
> 这个项目重点不是单纯做图表，而是保证数据准确、过程可追溯、异常能定位，比较贴合财务数据岗位的日常工作。

---

## 项目亮点

- 贴近义乌电商财务数据岗位实际场景
- 同时覆盖 Excel 实操和 Pandas 自动化
- 输出异常表和清洗日志，体现可追溯意识
- 结构简单，适合 1 天内跑通并用于面试讲解
