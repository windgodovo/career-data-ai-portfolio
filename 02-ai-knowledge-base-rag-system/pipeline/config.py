from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass
class RagSettings:
    llm_provider: str
    embedding_provider: str
    openai_api_key: str
    openai_base_url: str
    openai_api_keychain_service: str
    openai_api_keychain_account: str
    openai_model: str
    openai_embedding_model: str
    zhipu_api_key: str
    zhipu_base_url: str
    zhipu_api_keychain_service: str
    zhipu_api_keychain_account: str
    zhipu_model: str
    zhipu_embedding_model: str
    vector_db_dir: Path
    qa_audit_db: Path
    rag_top_k: int
    rag_min_score: float
    allowed_confidentiality: set[str]


def read_keychain_secret(service: str, account: str) -> str:
    if not service or not account:
        return ""

    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                service,
                "-a",
                account,
                "-w",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _normalize_provider(value: str, fallback: str = "openai") -> str:
    provider = (value or fallback).strip().lower()
    if provider not in {"openai", "zhipu"}:
        return fallback
    return provider


def load_settings() -> RagSettings:
    raw_conf = os.getenv("ALLOWED_CONFIDENTIALITY", "public,internal")
    conf_set = {v.strip() for v in raw_conf.split(",") if v.strip()}

    llm_provider = _normalize_provider(os.getenv("LLM_PROVIDER", "openai"), fallback="openai")
    embedding_provider = _normalize_provider(
        os.getenv("EMBEDDING_PROVIDER", llm_provider),
        fallback=llm_provider,
    )

    openai_keychain_service = os.getenv("OPENAI_API_KEYCHAIN_SERVICE", "rag-system")
    openai_keychain_account = os.getenv("OPENAI_API_KEYCHAIN_ACCOUNT", "siliconflow_api_key")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_api_key:
        openai_api_key = read_keychain_secret(openai_keychain_service, openai_keychain_account)

    zhipu_keychain_service = os.getenv("ZHIPU_API_KEYCHAIN_SERVICE", "rag-system")
    zhipu_keychain_account = os.getenv("ZHIPU_API_KEYCHAIN_ACCOUNT", "zhipu_api_key")
    zhipu_api_key = os.getenv("ZHIPU_API_KEY", "")
    if not zhipu_api_key:
        zhipu_api_key = read_keychain_secret(zhipu_keychain_service, zhipu_keychain_account)

    return RagSettings(
        llm_provider=llm_provider,
        embedding_provider=embedding_provider,
        openai_api_key=openai_api_key,
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1"),
        openai_api_keychain_service=openai_keychain_service,
        openai_api_keychain_account=openai_keychain_account,
        openai_model=os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "BAAI/bge-m3"),
        zhipu_api_key=zhipu_api_key,
        zhipu_base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
        zhipu_api_keychain_service=zhipu_keychain_service,
        zhipu_api_keychain_account=zhipu_keychain_account,
        zhipu_model=os.getenv("ZHIPU_MODEL", "glm-4.6"),
        zhipu_embedding_model=os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-3"),
        vector_db_dir=(ROOT_DIR / os.getenv("VECTOR_DB_DIR", "./data/chroma")).resolve(),
        qa_audit_db=(ROOT_DIR / os.getenv("QA_AUDIT_DB", "./data/ads/qa_audit.db")).resolve(),
        rag_top_k=int(os.getenv("RAG_TOP_K", "4")),
        rag_min_score=float(os.getenv("RAG_MIN_SCORE", "0.25")),
        allowed_confidentiality=conf_set,
    )
