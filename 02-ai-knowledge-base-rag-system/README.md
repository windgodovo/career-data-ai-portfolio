# 企业知识库 RAG 系统项目

这是一个面向企业文档问答场景的 AI 知识库与 RAG（检索增强生成）作品集项目。项目目标是解决企业制度、SOP、手册和内部知识文档难检索、难追溯、难审计的问题。

项目已经包含一个可运行的 MVP：从文档接入、切分、向量检索、引用溯源，到 FastAPI 查询接口和浏览器问答页面，形成一条完整的“文档 -> 检索 -> 回答 -> 审计”链路。

## 1. 项目目标

- 支持 `.pdf`、`.txt`、`.md` 等企业文档接入。
- 将文档切分为带元数据的语义块，保留来源、页码、章节、权限和 chunk id。
- 使用 Chroma 构建向量索引，实现语义检索。
- 通过 LLM 合成回答，并返回可追溯引用。
- 用 SQLite 记录查询日志、置信度和耗时，支持后续质量评估。
- 提供 FastAPI 接口和简单 Web UI，便于展示完整产品形态。

## 2. 业务场景

企业内部常见问题是：制度、合同、SOP、FAQ 分散在多个文件中，员工很难快速找到准确答案。传统关键词搜索容易漏掉同义表达，也很难判断答案是否来自可信文件。

```text
企业文档
  ↓
文档解析与语义切分
  ↓
向量索引与相似度检索
  ↓
引用约束下的 LLM 回答
  ↓
答案、引用、置信度、审计日志
```

## 3. 已实现功能

- 文档接入：支持 `.pdf`、`.txt`、`.md`。
- 语义切分：每个 chunk 带有 `source`、`page`、`section`、`owner`、`confidentiality`、`chunk_id`。
- 向量检索：使用 Chroma 存储与检索文档向量。
- 查询接口：FastAPI 提供 `/v1/query`。
- 引用溯源：回答返回文档来源、页码、章节、chunk id 和片段。
- 低置信度兜底：当检索证据不足时，避免强行编造答案。
- 审计日志：SQLite 保存查询、置信度、延迟等信息。
- Web UI：浏览器可直接访问问答页面。

## 4. 项目结构

```text
02-ai-knowledge-base-rag-system/
├── api/
│   ├── main.py          # FastAPI 入口
│   ├── rag_service.py   # 检索与答案合成
│   ├── schemas.py       # 请求与响应模型
│   └── log_store.py     # SQLite 审计日志
├── pipeline/
│   ├── config.py        # 配置管理
│   └── ingest.py        # 文档接入与向量索引构建
├── ui/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── data/
│   ├── chroma/          # 向量库
│   ├── dwd_chunks/      # chunk 预览快照
│   └── ads/             # 查询审计库
├── docs/
│   ├── RUNBOOK.md
│   └── samples/
│       └── company_policy.md
├── requirements.txt
└── README.md
```

## 5. 运行方式

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

如果使用 SiliconFlow + macOS Keychain，可以先写入密钥：

```bash
security add-generic-password -U -s rag-system -a siliconflow_api_key -w "<YOUR_SILICONFLOW_KEY>"
```

然后在 `.env` 中配置：

```bash
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEYCHAIN_SERVICE=rag-system
OPENAI_API_KEYCHAIN_ACCOUNT=siliconflow_api_key
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct
OPENAI_EMBEDDING_MODEL=BAAI/bge-m3
```

构建索引：

```bash
python -m pipeline.ingest --input-dir docs/samples --owner demo-team --confidentiality internal --reset
```

启动 API：

```bash
python -m uvicorn api.main:app --reload --port 8000
```

打开页面：

```text
http://127.0.0.1:8000/
```

更详细的操作步骤见 [docs/RUNBOOK.md](docs/RUNBOOK.md)。

## 6. API 示例

### POST `/v1/query`

请求示例：

```json
{
  "question": "年假有多少天？",
  "owner": "demo-team",
  "confidentiality": "internal",
  "top_k": 4,
  "use_web": false,
  "web_top_k": 3
}
```

响应包含：

- `answer`：答案正文。
- `citations`：引用来源、页码、章节、chunk id、分数和片段。
- `confidence`：回答置信度。
- `latency_ms`：查询耗时。
- `rewritten_question`：改写后的检索问题。

当 `use_web=true` 时，系统会额外执行联网搜索，并把网页摘要作为补充上下文；联网结果不会覆盖本地制度条款。

## 7. 数据治理映射

- ODS：`docs/samples/` 原始文档。
- DWD：`data/dwd_chunks/chunks_preview.json` 文档语义块。
- ADS：`data/ads/qa_audit.db` 查询审计数据。
- 血缘：通过 `chunk_id + source + page` 将答案追溯到原始文档位置。

## 8. 后续扩展

- 使用 PostgreSQL 管理多租户文档元数据和查询日志。
- 增加角色权限过滤和 API Key 鉴权。
- 增加批量评测集，评估忠实度、幻觉率和引用准确率。
- 增加定时重建索引流程。

## 9. 面试讲法

> 我做了一个企业知识库 RAG 系统，从企业制度文档接入开始，完成文档切分、元数据管理、向量索引、语义检索、引用约束回答和查询审计。这个项目不是只调用 LLM，而是重点保证答案可追溯、权限可过滤、低置信度可兜底，并通过 FastAPI 和 Web UI 做成可演示的业务系统。