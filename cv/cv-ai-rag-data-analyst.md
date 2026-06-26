# AI / RAG 数据应用方向 CV

## 个人信息

姓名：你的姓名  
邮箱：your.email@example.com  
GitHub：待补充  
LinkedIn：待补充  
目标岗位：AI Data Analyst / RAG Application Analyst / LLM Product Analyst / AI Solutions Analyst

## 个人简介

具备数据分析、数据工程和 AI 应用落地能力，能够围绕企业知识库、RAG 检索、查询审计和质量评估构建可演示的 AI 数据应用。熟悉文档切分、元数据管理、向量检索、引用溯源、FastAPI 接口和业务指标监控。

## 核心技能

- RAG：文档切分、chunk 元数据、向量索引、检索召回、引用约束回答。
- Python：FastAPI、Pandas、SQLite、日志审计、配置管理。
- 数据治理：ODS/DWD/ADS 分层、血缘追踪、置信度与质量指标。
- 产品分析：低置信度兜底、查询审计、用户问题分析、回答质量评估。

## 重点项目

### 企业知识库 RAG 系统

项目链接：`02-ai-knowledge-base-rag-system`

- 构建企业文档问答系统，支持 `.pdf`、`.txt`、`.md` 文档接入和语义切分。
- 为 chunk 保留 `source`、`page`、`section`、`owner`、`confidentiality`、`chunk_id` 等元数据。
- 使用 Chroma 构建向量索引，通过 FastAPI 提供 `/v1/query` 查询接口。
- 返回带引用的答案，包括来源、页码、章节、chunk id、相似度和片段，减少不可追溯回答。
- 使用 SQLite 记录查询日志、置信度和延迟，形成 ADS 审计层。
- 提供浏览器 UI，形成可演示的端到端 AI 应用。

### Excel AI 自动报表助手

项目链接：`03-excel-ai-auto-report-agent`

- 构建从 Excel / CSV 到 KPI、AI 摘要、报告输出和邮件发送的自动化链路。
- 当未配置 LLM Key 时提供本地兜底摘要，保证流程可运行。
- 适合展示 AI 在业务报表、运营分析和自动化交付中的落地能力。

## 面试表达

我做的 RAG 项目不是简单调用 LLM，而是把文档接入、语义切分、向量检索、引用溯源和查询审计串成完整系统。项目重点是答案可信、引用可追踪、低置信度可兜底，并能通过日志指标持续评估问答质量。
