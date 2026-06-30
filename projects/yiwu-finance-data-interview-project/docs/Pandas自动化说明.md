# Pandas 自动化说明

这个项目用 `finance_reconciliation_demo.py` 复现 Excel 中的清洗、对账和汇总流程。

## 运行方式

进入项目目录：

```bash
cd projects/yiwu-finance-data-interview-project
```

安装依赖：

```bash
pip install -r requirements.txt
```

运行脚本：

```bash
python finance_reconciliation_demo.py
```

---

## 脚本处理流程

脚本主要分为以下步骤：

1. 读取原始 CSV 数据
2. 删除空行
3. 按订单号去重
4. 统一日期格式
5. 清洗金额字段
6. 修正省份错别字
7. 按订单汇总退款金额
8. 合并订单、支付、退款三张表
9. 计算应收金额和差异金额
10. 判断异常原因
11. 输出财务日报、异常表和清洗日志

---

## 为什么这是面试加分项

Excel 可以证明你能完成基础实操；Pandas 可以证明你能把重复工作自动化。

面试时可以这样说：

> 如果只是临时处理，我会优先用 Excel，因为它直观、方便检查。  
> 如果这类报表每天都要重复做，我会用 Pandas 写成脚本，把清洗、汇总和异常输出自动化，减少人工复制粘贴和公式拖拽造成的错误。

---

## 输出文件

脚本会输出到：

```text
data/output/
├── clean_orders.csv
├── daily_finance_report.csv
├── reconciliation_alerts.csv
└── cleaning_log.csv
```
