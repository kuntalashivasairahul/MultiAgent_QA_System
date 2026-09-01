"""Retrieval over the Chroma index. Dense-only in v1; hybrid arrives in v2."""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ingest import get_vectorstore


def get_retriever(k: int = 5) -> VectorStoreRetriever:
    return get_vectorstore().as_retriever(search_kwargs={"k": k})


def format_docs(docs: list[Document]) -> str:
    """Render chunks with provenance so answers can cite and judges can check."""
    return "\n\n---\n\n".join(
        f"[source: {d.metadata.get('source')} | {d.metadata.get('headings')}]\n"
        f"{d.page_content}"
        for d in docs
    )
