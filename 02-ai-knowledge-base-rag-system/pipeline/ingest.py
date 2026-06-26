from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pipeline.config import ROOT_DIR, load_settings


SUPPORTED_EXTS = {".pdf", ".txt", ".md"}


def _sanitize_for_embedding(text: str) -> str:
    t = html.unescape(str(text or ""))
    t = t.replace("\ufeff", " ")

    # Strip html/style residues and noisy control chars before vectorization.
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\b[a-zA-Z_-]{2,}\s*=\s*\"[^\"]*\"", " ", t)
    t = re.sub(r"\b[a-zA-Z_-]{2,}\s*=\s*'[^']*'", " ", t)
    t = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", t)

    # Keep heading/newline structure, but remove markdown punctuation noise.
    t = re.sub(r"[\t\r]+", " ", t)
    t = re.sub(r"[ ]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = t.replace("�", " ")

    return t.strip()


def _iter_files(input_dir: Path) -> Iterable[Path]:
    for path in input_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            yield path


def _load_docs(path: Path) -> list[Document]:
    if path.suffix.lower() == ".pdf":
        return PyPDFLoader(str(path)).load()
    return TextLoader(str(path), encoding="utf-8").load()


def _guess_section(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "unknown"
    for ln in lines[:8]:
        if ln.startswith("#"):
            return ln.lstrip("#").strip()
    return lines[0][:80]


def build_chunks(
    input_dir: Path,
    owner: str,
    confidentiality: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    all_chunks: list[Document] = []
    for file_path in _iter_files(input_dir):
        raw_docs = _load_docs(file_path)
        cleaned_docs: list[Document] = []
        for d in raw_docs:
            cleaned = _sanitize_for_embedding(d.page_content)
            if not cleaned:
                continue
            cleaned_docs.append(Document(page_content=cleaned, metadata=dict(d.metadata)))

        doc_chunks = splitter.split_documents(cleaned_docs)

        for idx, chunk in enumerate(doc_chunks):
            source_name = file_path.name
            page = chunk.metadata.get("page", 0)
            section = _guess_section(chunk.page_content)
            chunk.metadata = {
                "source": source_name,
                "path": str(file_path.relative_to(ROOT_DIR)),
                "page": int(page) + 1,
                "owner": owner,
                "confidentiality": confidentiality,
                "section": section,
                "chunk_id": f"{source_name}:{page}:{idx}",
            }
            all_chunks.append(chunk)

    return all_chunks


def write_dwd_snapshot(chunks: list[Document]) -> Path:
    out_path = ROOT_DIR / "data" / "dwd_chunks" / "chunks_preview.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "content": c.page_content[:500],
            "metadata": c.metadata,
        }
        for c in chunks[:200]
    ]
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def ingest(input_dir: Path, owner: str, confidentiality: str, reset: bool) -> None:
    settings = load_settings()
    if settings.embedding_provider == "zhipu":
        emb_key = settings.zhipu_api_key
        emb_base = settings.zhipu_base_url
        emb_model = settings.zhipu_embedding_model
    else:
        emb_key = settings.openai_api_key
        emb_base = settings.openai_base_url
        emb_model = settings.openai_embedding_model

    if not emb_key:
        raise ValueError(
            f"Embedding provider={settings.embedding_provider} key is required. "
            "Configure env or keychain."
        )

    if confidentiality not in settings.allowed_confidentiality:
        raise ValueError(
            f"confidentiality must be one of {sorted(settings.allowed_confidentiality)}"
        )

    chunks = build_chunks(
        input_dir=input_dir,
        owner=owner,
        confidentiality=confidentiality,
        chunk_size=1000,
        chunk_overlap=150,
    )

    if not chunks:
        print("No supported documents found.")
        return

    embeddings = OpenAIEmbeddings(
        model=emb_model,
        api_key=emb_key,
        base_url=(emb_base or None),
    )
    settings.vector_db_dir.mkdir(parents=True, exist_ok=True)

    if reset:
        db = Chroma(
            collection_name="kb_docs",
            embedding_function=embeddings,
            persist_directory=str(settings.vector_db_dir),
        )
        db.delete_collection()

    db = Chroma(
        collection_name="kb_docs",
        embedding_function=embeddings,
        persist_directory=str(settings.vector_db_dir),
    )
    db.add_documents(chunks)

    snapshot = write_dwd_snapshot(chunks)
    print(f"Indexed chunks: {len(chunks)}")
    print(f"Vector DB: {settings.vector_db_dir}")
    print(f"Chunk snapshot: {snapshot}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest local docs into Chroma for RAG")
    parser.add_argument(
        "--input-dir",
        default=str(ROOT_DIR / "docs" / "samples"),
        help="Input directory containing PDF/TXT/MD files",
    )
    parser.add_argument("--owner", default="demo-team", help="Document owner tag")
    parser.add_argument(
        "--confidentiality",
        default="internal",
        help="Metadata tag such as public/internal",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing collection before indexing",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ingest(
        input_dir=Path(args.input_dir).resolve(),
        owner=args.owner,
        confidentiality=args.confidentiality,
        reset=args.reset,
    )
