from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    owner: str | None = None
    confidentiality: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=12)
    use_web: bool = False
    web_top_k: int = Field(default=3, ge=1, le=5)


class Citation(BaseModel):
    chunk_id: str
    source: str
    page: int
    section: str
    score: float
    snippet: str


class QueryResponse(BaseModel):
    request_id: str
    answer: str
    confidence: float
    latency_ms: int
    rewritten_question: str
    citations: list[Citation]


class MetricsResponse(BaseModel):
    total_queries: int
    avg_latency_ms: float
    avg_confidence: float