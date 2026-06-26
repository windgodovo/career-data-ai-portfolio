# RUNBOOK

## Purpose

This runbook explains how to set up, run, and troubleshoot the AI Knowledge Base RAG System in a local macOS development environment.

## 1. Prerequisites

Required:
- Python 3.13+
- macOS Keychain access
- A valid SiliconFlow API key

Recommended:
- Terminal opened in project root
- Stable network connection for embeddings and LLM calls

Project root:

```bash
cd "/Volumes/new/vibe code/work finding/new work/02-ai-knowledge-base-rag-system"
```

## 2. Create Local Virtual Environment

Create a project-local `.venv`:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Verify the interpreter:

```bash
which python
python -V
python -m pip --version
```

Expected result:
- `which python` should point to `.venv/bin/python`

## 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you only need to install one missing package:

```bash
python -m pip install fastapi uvicorn
```

## 4. Configure API Key with macOS Keychain

Store the SiliconFlow key in Keychain:

```bash
security add-generic-password -U -s rag-system -a siliconflow_api_key -w "<YOUR_SILICONFLOW_KEY>"
```

The project reads this key using:
- service: `rag-system`
- account: `siliconflow_api_key`

## 5. Configure Environment File

If `.env` does not exist:

```bash
cp .env.example .env
```

Expected SiliconFlow configuration:

```env
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEYCHAIN_SERVICE=rag-system
OPENAI_API_KEYCHAIN_ACCOUNT=siliconflow_api_key
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct
OPENAI_EMBEDDING_MODEL=BAAI/bge-m3
RAG_TOP_K=4
RAG_MIN_SCORE=0.25
VECTOR_DB_DIR=./data/chroma
QA_AUDIT_DB=./data/ads/qa_audit.db
ALLOWED_CONFIDENTIALITY=public,internal
```

## 6. Verify Effective Runtime Config

```bash
python - <<'PY'
from pipeline.config import load_settings
s = load_settings()
print('llm_provider =', s.llm_provider)
print('embedding_provider =', s.embedding_provider)
print('openai_base_url =', s.openai_base_url)
print('openai_keychain_account =', s.openai_api_keychain_account)
print('openai_model =', s.openai_model)
print('openai_embedding_model =', s.openai_embedding_model)
print('openai_key_set =', bool(s.openai_api_key), 'len=', len(s.openai_api_key or ''))
PY
```

Expected result:
- `llm_provider = openai`
- `embedding_provider = openai`
- `openai_base_url = https://api.siliconflow.cn/v1`
- `openai_key_set = True`

## 7. Build Vector Index

```bash
python -m pipeline.ingest --input-dir docs/samples --owner demo-team --confidentiality internal --reset
```

Expected outputs:
- Chroma data written under `data/chroma/`
- Chunk snapshot written to `data/dwd_chunks/chunks_preview.json`

## 8. Start API Server

Always use the virtual environment interpreter:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Do not use global `uvicorn` if your dependencies were installed into `.venv`.

One-click start (recommended):

```bash
./scripts/start.sh
```

Custom port:

```bash
./scripts/start.sh 8001
```

## 9. Open the Web UI

Open in browser:

```text
http://127.0.0.1:8000/
```

## 10. Run a Direct Query Test

```bash
python - <<'PY'
from api.rag_service import build_deps, query_rag
from api.schemas import QueryRequest

deps = build_deps()
resp = query_rag(
    deps,
    QueryRequest(
        question='公司年假一共多少天',
        owner='demo-team',
        confidentiality='internal',
        top_k=4,
    ),
)
print('answer =', resp.answer)
print('confidence =', resp.confidence)
print('citations =', len(resp.citations))
for c in resp.citations[:1]:
    print('top citation =', c.source, c.page, c.section, c.score)
PY
```

    Optional: test online-augmented mode

    ```bash
    python - <<'PY'
    from api.rag_service import build_deps, query_rag
    from api.schemas import QueryRequest

    deps = build_deps()
    resp = query_rag(
        deps,
        QueryRequest(
            question='采购标准有哪些',
            owner='demo-team',
            confidentiality='internal',
            top_k=4,
            use_web=True,
            web_top_k=3,
        ),
    )
    print('answer =', resp.answer)
    print('web citations =', [c.source for c in resp.citations if c.chunk_id.startswith('web:')])
    PY
    ```

    Notes:
    - `use_web=True` adds web snippets as supplementary context only.
    - If network search returns empty, the system keeps local RAG behavior.
    - Keep `web_top_k` small (2-3) to control latency.

## 11. Common Issues

### A. `ModuleNotFoundError: No module named 'fastapi'`

Cause:
- Global `uvicorn` or wrong interpreter is being used.

Fix:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

### B. `python3 pip install ...` fails

Cause:
- Wrong command format.

Fix:

```bash
python3 -m pip install -r requirements.txt
```

### C. `429` or provider balance error during ingest

Cause:
- Embedding provider quota is insufficient.

Fix:
- Check SiliconFlow account status
- Confirm embedding model is enabled
- Retry after verifying provider access

### D. Answer quality is fragmented or unnatural

Possible causes:
- Retrieved chunks contain markdown noise
- Prompt is too loose
- Top chunk similarity is low

Suggested checks:
- inspect `data/dwd_chunks/chunks_preview.json`
- reduce `top_k`
- improve answer prompt and chunk cleaning

### E. `Exit Code 146`

Cause:
- Process was suspended, often by `Ctrl+Z`.

Fix:
- rerun the command normally
- avoid suspending long-running servers unless intended

### F. `[Errno 48] Address already in use` and page not opening

Cause:
- A stale Python/uvicorn process is still listening on port 8000.
- The old process may be hung, so the port is occupied but requests time out.

Fix:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill -9 <PID1> <PID2>
python -m uvicorn api.main:app --reload --port 8000
```

Verify health:

```bash
curl -sS http://127.0.0.1:8000/health

### G. `use_web=True` but no web citations returned

Cause:
- Network access may be unavailable in current environment.
- External search provider may throttle or return no suitable snippets.

Fix:

```bash
python -m pip install -r requirements.txt
python - <<'PY'
from api.rag_service import _search_web_snippets
print(_search_web_snippets('采购标准', 2))
PY
```

If still empty, treat online mode as optional and continue with local citations.
```

## 12. Shutdown

If the server is running in foreground:

```bash
Ctrl+C
```

Deactivate virtual environment when done:

```bash
deactivate
```

One-click stop by port:

```bash
./scripts/stop.sh
```

Custom port stop:

```bash
./scripts/stop.sh 8001
```
