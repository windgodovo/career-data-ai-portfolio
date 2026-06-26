from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.log_store import AuditStore
from api.rag_service import RagDeps, build_deps, query_rag
from api.schemas import MetricsResponse, QueryRequest, QueryResponse

app = FastAPI(title="AI Knowledge Base RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


deps: RagDeps | None = None
audit: AuditStore | None = None


@app.on_event("startup")
def startup_event() -> None:
    global deps, audit
    deps = build_deps()
    audit = AuditStore(deps.settings.qa_audit_db)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/query", response_model=QueryResponse)
def ask(req: QueryRequest) -> QueryResponse:
    if deps is None or audit is None:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        resp = query_rag(deps, req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {exc}") from exc

    audit.add_row(
        request_id=resp.request_id,
        question=req.question,
        rewritten_question=resp.rewritten_question,
        answer=resp.answer,
        confidence=resp.confidence,
        latency_ms=resp.latency_ms,
        citation_count=len(resp.citations),
    )
    return resp


@app.get("/v1/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    if audit is None:
        raise HTTPException(status_code=500, detail="Audit store not ready")

    total, avg_latency, avg_conf = audit.metrics()
    return MetricsResponse(
        total_queries=total,
        avg_latency_ms=round(avg_latency, 2),
        avg_confidence=round(avg_conf, 4),
    )


UI_DIR = Path(__file__).resolve().parent.parent / "ui"
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


@app.get("/")
def root_ui() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")
