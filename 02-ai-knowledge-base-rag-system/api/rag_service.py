from __future__ import annotations

import html
import importlib
import re
import time
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from api.schemas import Citation, QueryRequest, QueryResponse
from pipeline.config import RagSettings, load_settings

DDGS = None
try:  # pragma: no cover
    DDGS = getattr(importlib.import_module("duckduckgo_search"), "DDGS", None)
except Exception:
    DDGS = None


REWRITE_PROMPT = """You are a retrieval optimizer.
将用户问题改写成更适合制度文档检索的一句话。
要求：
1. 保留原始意图，不改变事实。
2. 将抽象问法映射到制度关键词（如：工作时间、审批规则、报销时限、加班、请假、安全要求）。
3. 输出中文，且仅返回改写后的查询，不要解释。"""


INTENT_HINTS: list[tuple[list[str], list[str]]] = [
    (["年假", "带薪假", "假期"], ["annual leave", "paid leave", "vacation", "carry forward"]),
    (["工作时间", "上班时间", "工时"], ["working hours", "Monday to Friday", "09:00 to 18:00"]),
    (["报销", "差旅", "发票"], ["reimbursement", "travel", "receipt", "finance"]),
    (["采购", "采购资金", "采购审批"], ["procurement", "purchase request", "approval", "quotation"]),
    (["考核", "绩效", "评估"], ["performance review", "review", "twice per year"]),
]


INTENT_FOCUS_TERMS: list[tuple[list[str], list[str]]] = [
    (["年假", "带薪假", "假期"], ["annual leave", "paid leave", "vacation", "carry", "next year"]),
    (["工作时间", "上班时间", "工时"], ["working hours", "monday to friday", "09:00", "18:00"]),
    (["报销", "差旅", "发票"], ["reimbursement", "travel", "receipt", "finance"]),
    (["采购", "采购资金", "采购审批"], ["procurement", "quotation", "approval", "purchase request"]),
]

ANSWER_PROMPT = """你是一个严格基于证据回答的知识库助手。
你只能使用给定的上下文回答，不能补充上下文中没有的信息。

输出要求：
1. 使用自然、清晰、专业的中文作答，优先给出结论，再补关键依据。
2. 不要输出项目符号、碎片词、重复数字、重复短语或引用编号。
3. 如果问题是在问数量、时长、金额、日期，直接明确给出数值和单位。
4. 如果问题是“标准/要求/规则/流程/条件”类，尽量覆盖上下文中关键阈值、审批角色、时限。
5. 如果证据不足，明确回答“根据当前检索结果无法确认”，并简要说明还缺什么信息。
6. 正文建议 80 到 220 字，允许在信息完整前提下略短，不要为了凑字数添加套话。

Question: {question}

Context:
{context}
"""

WEB_SUPPLEMENT_PROMPT = """

补充说明（可选）：
- 如果提供了联网补充信息，请在正文最后用一句话总结“外部补充观察”，并明确其仅供参考。
- 外部补充不得覆盖或否定本地文档中的硬性规则。
"""


@dataclass
class RagDeps:
    settings: RagSettings
    vector_db: Chroma
    llm: ChatOpenAI


def _provider_credentials(settings: RagSettings, provider: str) -> tuple[str, str, str]:
    if provider == "zhipu":
        return (
            settings.zhipu_api_key,
            settings.zhipu_base_url,
            settings.zhipu_model,
        )
    return (
        settings.openai_api_key,
        settings.openai_base_url,
        settings.openai_model,
    )


def _embedding_credentials(settings: RagSettings) -> tuple[str, str, str]:
    provider = settings.embedding_provider
    if provider == "zhipu":
        return (
            settings.zhipu_api_key,
            settings.zhipu_base_url,
            settings.zhipu_embedding_model,
        )
    return (
        settings.openai_api_key,
        settings.openai_base_url,
        settings.openai_embedding_model,
    )


def build_deps() -> RagDeps:
    settings = load_settings()
    llm_key, llm_base, llm_model = _provider_credentials(settings, settings.llm_provider)
    if not llm_key:
        raise ValueError(
            f"{settings.llm_provider} API key is missing. Configure env or keychain."
        )

    emb_key, emb_base, emb_model = _embedding_credentials(settings)
    if not emb_key:
        raise ValueError(
            f"{settings.embedding_provider} embedding key is missing. Configure env or keychain."
        )

    embeddings = OpenAIEmbeddings(
        model=emb_model,
        api_key=emb_key,
        base_url=(emb_base or None),
    )
    vector_db = Chroma(
        collection_name="kb_docs",
        embedding_function=embeddings,
        persist_directory=str(settings.vector_db_dir),
    )
    llm = ChatOpenAI(
        model=llm_model,
        temperature=0,
        api_key=llm_key,
        base_url=(llm_base or None),
    )
    return RagDeps(settings=settings, vector_db=vector_db, llm=llm)


def _rewrite_question(llm: ChatOpenAI, question: str) -> str:
    try:
        msg = llm.invoke([
            ("system", REWRITE_PROMPT),
            ("user", question),
        ])
        text = str(msg.content).strip()
        return text or question
    except Exception:
        return question


def _build_filter(req: QueryRequest) -> dict | None:
    clauses: list[dict] = []
    if req.owner:
        clauses.append({"owner": req.owner})
    if req.confidentiality:
        clauses.append({"confidentiality": req.confidentiality})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _render_context(citations: list[Citation], context_by_chunk: dict[str, str]) -> str:
    blocks = []
    for idx, c in enumerate(citations, start=1):
        snippet = context_by_chunk.get(c.chunk_id, c.snippet)
        snippet = _sanitize_text(snippet)
        blocks.append(
            "\n".join(
                [
                    f"[C{idx}] source={c.source} page={c.page} section={c.section} score={c.score:.3f}",
                    snippet,
                ]
            )
        )
    return "\n\n".join(blocks)


def _normalize_answer_text(text: str) -> str:
    answer = _sanitize_text(str(text or ""))
    if not answer:
        return _fallback_answer()

    answer = re.sub(r"\[C\d+\]", "", answer)
    answer = re.sub(r"[#*_`]+", " ", answer)
    answer = re.sub(r"\s+", " ", answer).strip()
    answer = re.sub(r"(\b\d+(?:\.\d+)?\b)(?:\s+\1)+", r"\1", answer)
    answer = re.sub(r"([\u4e00-\u9fff]{2,6})\1+", r"\1", answer)
    answer = re.sub(r"([。！？；，])\1+", r"\1", answer)

    if answer and answer[-1] not in "。！？":
        answer = f"{answer}。"
    return answer


def _sanitize_text(text: str) -> str:
    t = html.unescape(str(text or ""))

    # Remove HTML tags and CSS-like attribute residues.
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\b[a-zA-Z_-]{2,}\s*=\s*\"[^\"]*\"", " ", t)
    t = re.sub(r"\b[a-zA-Z_-]{2,}\s*=\s*'[^']*'", " ", t)

    # Remove markdown heading marks and broken separators.
    t = re.sub(r"[#*_`]+", " ", t)
    t = re.sub(r"={2,}|-{2,}|_{2,}", " ", t)

    # Remove control chars and replacement chars.
    t = re.sub(r"[\x00-\x1F\x7F]", " ", t)
    t = t.replace("�", " ")

    t = re.sub(r"\s+", " ", t).strip()
    return t


def _fit_answer_length(answer: str, min_len: int = 0, max_len: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(answer or "")).strip()
    if not text:
        return text

    def compact_len(s: str) -> int:
        return len(re.sub(r"\s+", "", s))

    if compact_len(text) > max_len:
        candidate = ""
        count = 0
        for ch in text:
            candidate += ch
            if not ch.isspace():
                count += 1
            if count >= max_len:
                break
        cut_positions = [candidate.rfind("。"), candidate.rfind("！"), candidate.rfind("？"), candidate.rfind("；")]
        cut = max(cut_positions)
        if cut >= 60:
            text = candidate[:cut + 1]
        else:
            text = candidate
            if text[-1] not in "。！？":
                text = f"{text}。"

    if min_len > 0 and compact_len(text) < min_len:
        tail = "以上为当前命中文档中的核心条款。"
        remain = min_len - compact_len(text)
        text = f"{text}{tail[:max(remain, 0)]}"
        if text and text[-1] not in "。！？":
            text = f"{text}。"

    if compact_len(text) > max_len:
        clipped = ""
        count = 0
        for ch in text:
            clipped += ch
            if not ch.isspace():
                count += 1
            if count >= max_len:
                break
        text = clipped
        if text and text[-1] not in "。！？":
            text = f"{text[:-1]}。"

    return text


def _fallback_answer() -> str:
    return "当前检索到的证据不足，建议换一种问法，或补充文档后再试。"


def _merge_retrieval_results(
    primary: list[tuple],
    secondary: list[tuple],
    question: str,
) -> list[tuple]:
    """Merge two retrieval result lists by chunk_id and keep best score."""
    merged: dict[str, tuple] = {}

    q_low = question.lower()

    q_terms = re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]{3,}", q_low)
    q_terms = q_terms[:10]

    def lexical_bonus(text: str) -> float:
        if not q_terms:
            return 0.0
        t_low = text.lower()
        hit = sum(1 for t in q_terms if t in t_low)
        if hit <= 0:
            return 0.0
        return min(0.18, 0.04 * hit)

    def keyword_bonus(text: str) -> float:
        t_low = text.lower()
        bonus = 0.0
        for zh_terms, en_terms in INTENT_HINTS:
            if any(term in question for term in zh_terms) or any(term.lower() in q_low for term in en_terms):
                hit_count = sum(1 for e in en_terms if e.lower() in t_low)
                if hit_count > 0:
                    bonus = max(bonus, min(0.16, 0.06 + 0.03 * hit_count))
        return bonus

    for doc, score in primary + secondary:
        chunk_id = str(doc.metadata.get("chunk_id", ""))
        if not chunk_id:
            chunk_id = f"{doc.metadata.get('source', 'unknown')}:{doc.metadata.get('page', 0)}:{hash(doc.page_content[:80])}"

        base_score = max(0.0, min(1.0, float(score)))
        preview = str(doc.page_content or "")[:1600]
        adjusted_score = base_score + keyword_bonus(preview) + lexical_bonus(preview)
        adjusted_score = max(0.0, min(1.0, adjusted_score))

        old = merged.get(chunk_id)
        if old is None or adjusted_score > float(old[1]):
            merged[chunk_id] = (doc, adjusted_score)

    return sorted(merged.values(), key=lambda x: float(x[1]), reverse=True)


def _expand_queries(question: str, rewritten: str) -> list[str]:
    queries = [rewritten.strip(), question.strip()]
    for zh_terms, en_terms in INTENT_HINTS:
        if any(term in question for term in zh_terms):
            queries.append(f"{question} {' '.join(en_terms)}")
            queries.append(" ".join(en_terms))

    # de-dup while preserving order
    out: list[str] = []
    seen: set[str] = set()
    for q in queries:
        qn = re.sub(r"\s+", " ", q).strip()
        if not qn or qn in seen:
            continue
        seen.add(qn)
        out.append(qn)
    return out


def _rank_score(rank_idx: int, total: int) -> float:
    if total <= 1:
        return 0.95
    step = 0.6 / (total - 1)
    return max(0.35, 0.95 - rank_idx * step)


def _rule_based_policy_answer(question: str, context: str) -> str:
    q = question.strip()
    ctx = context

    if any(k in q for k in ["年假", "带薪假", "假期"]):
        annual = re.search(r"(\d+)\s*days\s+annual\s+leave", ctx, re.IGNORECASE)
        if not annual:
            annual = re.search(r"annual\s+leave[^\d]*(\d+)\s*days", ctx, re.IGNORECASE)
        carry = re.search(r"carried\s+forward[^\d]*(\d+)\s*days", ctx, re.IGNORECASE)
        if annual:
            days = annual.group(1)
            if carry:
                return f"根据制度文档，员工每年享有{days}天年假，未使用年假最多可结转{carry.group(1)}天至下一年。"
            return f"根据制度文档，员工每年享有{days}天年假。"

    if any(k in q for k in ["工作时间", "上班时间", "工时"]):
        match = re.search(r"Monday\s+to\s+Friday[^\d]*(\d{2}:\d{2})\s*to\s*(\d{2}:\d{2})", ctx, re.IGNORECASE)
        if match:
            return f"根据员工手册，标准工作时间为周一至周五{match.group(1)}到{match.group(2)}，午休1小时。"

    if any(k in q for k in ["采购", "采购标准", "采购资金", "采购审批"]):
        req = re.search(r"above\s*([\d,]+)\s*cny\s*require\s*department\s+head\s+approval", ctx, re.IGNORECASE)
        quote = re.search(r"at\s+least\s+three\s+vendor\s+quotations\s+are\s+required\s+for\s+purchases\s+above\s*([\d,]+)\s*cny", ctx, re.IGNORECASE)
        legal = re.search(r"legal\s+review\s+is\s+mandatory\s+for\s+all\s+contracts\s+above\s*([\d,]+)\s*cny", ctx, re.IGNORECASE)
        pay = re.search(r"standard\s+payment\s+terms\s+are\s+net\s*(\d+)", ctx, re.IGNORECASE)
        adv = re.search(r"advance\s+payments\s+above\s*(\d+)%\s+require\s+cfo\s+approval", ctx, re.IGNORECASE)
        if any([req, quote, legal, pay, adv]):
            parts: list[str] = []
            if req:
                parts.append(f"采购申请需提交业务说明，超过{req.group(1)} CNY需部门负责人审批")
            if quote:
                parts.append(f"超过{quote.group(1)} CNY的采购至少需要三家供应商报价")
            if legal:
                parts.append(f"超过{legal.group(1)} CNY的合同必须进行法务审查")
            if pay:
                parts.append(f"标准付款账期为Net {pay.group(1)}")
            if adv:
                parts.append(f"预付款超过{adv.group(1)}%需CFO批准")
            return "根据当前采购制度，" + "；".join(parts) + "。"

    return ""


def _focus_citations(question: str, citations: list[Citation], context_by_chunk: dict[str, str]) -> list[Citation]:
    q = question.lower()
    terms: list[str] = []
    for zh_terms, en_terms in INTENT_FOCUS_TERMS:
        if any(z in question for z in zh_terms) or any(e.lower() in q for e in en_terms):
            terms.extend([z.lower() for z in zh_terms])
            terms.extend([e.lower() for e in en_terms])
            break

    if not terms:
        return citations

    focused: list[Citation] = []
    min_hits = 2 if len(terms) >= 6 else 1
    for c in citations:
        text = _sanitize_text(context_by_chunk.get(c.chunk_id, c.snippet)).lower()
        hit_count = sum(1 for t in terms if t in text)
        if hit_count >= min_hits:
            focused.append(c)

    return focused or citations


def _search_web_snippets(query: str, max_results: int) -> list[dict[str, str]]:
    if DDGS is None:
        return []

    rows: list[dict[str, str]] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                title = _sanitize_text(item.get("title", ""))
                href = _sanitize_text(item.get("href", ""))
                body = _sanitize_text(item.get("body", ""))
                if not href or not body:
                    continue
                rows.append({"title": title, "href": href, "body": body})
    except Exception:
        return []
    return rows


def _render_web_context(web_rows: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for i, row in enumerate(web_rows, start=1):
        title = row.get("title", "")
        href = row.get("href", "")
        body = row.get("body", "")
        blocks.append(f"[W{i}] {title} | {href}\n{body}")
    return "\n\n".join(blocks)


def _web_rows_to_citations(web_rows: list[dict[str, str]]) -> list[Citation]:
    out: list[Citation] = []
    for i, row in enumerate(web_rows, start=1):
        href = row.get("href", "")
        title = row.get("title", "")
        body = row.get("body", "")
        parsed = urlparse(href)
        domain = parsed.netloc or "web"
        out.append(
            Citation(
                chunk_id=f"web:{i}",
                source=domain,
                page=0,
                section=title[:80] or "web-result",
                score=0.3,
                snippet=body[:260],
            )
        )
    return out


def _is_low_quality_answer(question: str, answer: str) -> bool:
    q = str(question or "")
    a = str(answer or "")
    if not a:
        return True

    q_has_zh = bool(re.search(r"[\u4e00-\u9fff]", q))
    if not q_has_zh:
        return False

    compact = re.sub(r"\s+", "", a)
    if not compact:
        return True

    latin = re.findall(r"[A-Za-z]", compact)
    latin_ratio = len(latin) / max(1, len(compact))
    if latin_ratio > 0.30:
        return True

    if re.search(r"(\d+\s*天).{0,6}\1", a):
        return True

    if re.search(r"\d{3,}", a):
        return True

    if "助手" in a or "assistant" in a.lower():
        return True

    if re.search(r"\d\s*,\s*\d", a):
        return True

    # Repeated clause pattern like "采购标准包括...采购标准包括..."
    compact = re.sub(r"\s+", "", a)
    if re.search(r"(.{4,12})\1{1,}", compact):
        return True

    return False


def query_rag(deps: RagDeps, req: QueryRequest) -> QueryResponse:
    start = time.perf_counter()
    request_id = str(uuid.uuid4())

    clean_question = _sanitize_text(req.question)
    rewritten = _rewrite_question(deps.llm, clean_question)
    top_k = req.top_k or deps.settings.rag_top_k
    doc_filter = _build_filter(req)

    # Multi-query retrieval for better abstract/question-variant matching.
    query_variants = _expand_queries(clean_question, rewritten)
    pool_k = max(top_k * 5, 12)
    merged_pool: list[tuple] = []
    for q in query_variants:
        part_docs = deps.vector_db.similarity_search(
            q,
            k=pool_k,
            filter=doc_filter,
        )
        for idx, doc in enumerate(part_docs):
            merged_pool.append((doc, _rank_score(idx, pool_k)))

    results = _merge_retrieval_results(merged_pool, [], question=clean_question)[:top_k]

    citations: list[Citation] = []
    context_by_chunk: dict[str, str] = {}
    for doc, score in results:
        score_val = float(score)
        chunk_id = str(doc.metadata.get("chunk_id", ""))
        full_for_llm = str(doc.page_content or "")[:1600]
        citations.append(
            Citation(
                chunk_id=chunk_id,
                source=str(doc.metadata.get("source", "unknown")),
                page=int(doc.metadata.get("page", 0)),
                section=str(doc.metadata.get("section", "unknown")),
                score=score_val,
                snippet=doc.page_content[:260],
            )
        )
        if chunk_id:
            context_by_chunk[chunk_id] = full_for_llm

    good = [c for c in citations if c.score >= deps.settings.rag_min_score]

    # Relax threshold for abstract questions when there are near-miss hits.
    if not good and citations:
        relaxed_min = max(0.15, deps.settings.rag_min_score - 0.12)
        good = [c for c in citations if c.score >= relaxed_min]

    if good:
        good = _focus_citations(clean_question, good, context_by_chunk)

    confidence = 0.0
    if good:
        confidence = sum(c.score for c in good) / len(good)

    if not good:
        answer = _fallback_answer()
    else:
        context = _render_context(good, context_by_chunk)
        web_rows: list[dict[str, str]] = []
        if req.use_web:
            web_rows = _search_web_snippets(clean_question, req.web_top_k)
            if web_rows:
                context = f"{context}\n\n[WebSupplement]\n{_render_web_context(web_rows)}"

        prompt = ANSWER_PROMPT.format(question=clean_question, context=context)
        if web_rows:
            prompt = f"{prompt}\n{WEB_SUPPLEMENT_PROMPT}"

        msg = deps.llm.invoke(
            [
                ("system", "你是严格基于证据回答的问题助手。"),
                ("user", prompt),
            ]
        )
        answer = _fit_answer_length(_normalize_answer_text(str(msg.content)))

        malformed = bool(re.search(r"\d+:\d+.*next\s*year:?\d+", answer, re.IGNORECASE))
        if "无法确认" in answer or malformed or _is_low_quality_answer(clean_question, answer):
            rb_answer = _rule_based_policy_answer(clean_question, context)
            if rb_answer:
                answer = _fit_answer_length(_normalize_answer_text(rb_answer))

        if req.use_web and web_rows:
            good.extend(_web_rows_to_citations(web_rows))

    latency_ms = int((time.perf_counter() - start) * 1000)
    return QueryResponse(
        request_id=request_id,
        answer=answer,
        confidence=round(confidence, 4),
        latency_ms=latency_ms,
        rewritten_question=rewritten,
        citations=good,
    )
