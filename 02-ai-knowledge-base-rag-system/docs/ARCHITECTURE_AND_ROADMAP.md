# Architecture And Roadmap

## 1. 项目定位

本项目是一个“本地知识库优先、可选联网补充”的 RAG 问答系统。
核心目标：
- 对制度文档进行结构化检索
- 让回答带有引用依据与可追溯性
- 在本地可稳定运行并可持续迭代

## 2. 分层架构（与你当前代码一一对应）

### 2.1 接口层（API + UI）
- API 入口：api/main.py
- 前端页面：ui/index.html, ui/app.js, ui/styles.css

职责：
- 提供 /v1/query, /v1/metrics, /health
- 负责用户交互、请求发起、结果展示
- 提供“思考进度可视化”来改善等待体验

### 2.2 引擎层（RAG 核心）
- 核心引擎：api/rag_service.py
- 协议模型：api/schemas.py

职责：
- 问题清洗与改写
- 多查询检索与重排
- 答案生成、后处理、质量兜底
- 可选联网补充（use_web）

### 2.3 配置与依赖层
- 配置中心：pipeline/config.py

职责：
- 统一管理 Provider、模型、阈值、路径
- 从环境变量和 macOS Keychain 读取密钥
- 将“运行策略”从业务逻辑中解耦

### 2.4 数据构建层（离线）
- 入库构建：pipeline/ingest.py

职责：
- 读取 PDF/TXT/MD
- 清洗文本、切块、打元数据
- 写入向量库 Chroma
- 产出 DWD 快照供核查

### 2.5 存储与审计层
- 审计存储：api/log_store.py
- 数据目录：data/chroma, data/dwd_chunks, data/ads

职责：
- 保存问答审计记录（request_id, latency, confidence 等）
- 提供运营指标与质量回看基础

### 2.6 运维脚本层
- 启停脚本：scripts/start.sh, scripts/stop.sh
- 运维文档：docs/RUNBOOK.md

职责：
- 一键启动/停止、端口冲突清理
- 将“可运行性”固化成标准动作

## 3. 运行时流程（在线 Query）

1. 前端将问题提交到 /v1/query。
2. main.py 调用 query_rag。
3. rag_service.py 执行：
   - 问题清洗与改写
   - 多查询召回 + 重排
   - 证据过滤与上下文拼装
   - LLM 生成 + 后处理 + 质量检测
   - 必要时走规则兜底
4. 返回 answer + citations + confidence + latency。
5. log_store.py 将结果写入 qa_audit。
6. /v1/metrics 聚合审计数据用于监控。

## 4. 数据分层逻辑（ODS / DWD / ADS）

- ODS：原始文档（docs/samples 或外部输入）
- DWD：清洗分块后快照（data/dwd_chunks/chunks_preview.json）
- ADS：问答审计指标（data/ads/qa_audit.db）

设计价值：
- 能追踪“答案来自哪段文档”
- 能复盘“为什么答得好/不好”
- 能支持后续评估与治理

## 5. 当前设计优点与边界

### 优点
- 分层清晰，接口与引擎解耦
- 支持多 Provider 切换
- 引用与审计链路完整
- 本地部署门槛低，适合快速迭代

### 边界
- 目前更偏单租户、单机部署
- 检索与重排策略主要为规则增强
- 联网补充不保证稳定命中
- 缺少系统化评测流水线

## 6. 扩展路线图（按优先级）

### P0：稳定性与可观测性
- 引入结构化日志（JSON logs）
- 增加请求级追踪字段（trace_id）
- 提供 /v1/debug/retrieval 便于排查召回问题

### P1：检索质量升级
- 从单一向量召回升级为“向量 + 关键词混合召回”
- 加入 Cross-Encoder 重排
- 提供可配置的意图词典和阈值策略

### P2：回答质量升级
- 增加“回答事实一致性检查”
- 将规则兜底从硬编码转为可配置模板
- 对回答做更细粒度的段落级引用映射

### P3：数据与平台化
- 将审计库迁移到 PostgreSQL
- 增加多租户元数据隔离
- 引入定时增量重建索引任务

### P4：安全与治理
- 接入 API Key 鉴权 / RBAC
- 根据 confidentiality 做服务端强制过滤
- 增加敏感信息检测与脱敏策略

## 7. 推荐的下一步实施顺序

1. 做 P0：先让问题可观测、可诊断。
2. 做 P1：优先提升召回与重排准确率。
3. 做 P2：减少“答非所问/答不全”问题。
4. 最后推进 P3/P4：走向生产化与治理化。

## 8. 维护建议

- 每次修改 rag_service.py 后，固定跑两类回归问题：
  - 事实数值类（如年假天数）
  - 流程标准类（如采购审批）
- 将每次调优结果记录到 docs 中，形成可追溯变更历史。
- 保持 .env.example 与 RUNBOOK 同步更新，避免运行偏差。
