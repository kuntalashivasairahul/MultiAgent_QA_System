"""Dense retrieval over a verified public-corpus snapshot."""
from __future__ import annotations

import json
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ingest import get_vectorstore


@lru_cache(maxsize=8)
def _retriever(store, k: int) -> VectorStoreRetriever:
    return store.as_retriever(search_kwargs={"k": k})


def get_retriever(k: int = 5) -> VectorStoreRetriever:
    if k < 1:
        raise ValueError("k must be positive")
    return _retriever(get_vectorstore(), k)


def format_docs(docs: list[Document]) -> str:
    """JSON-encode untrusted source data and give each retrieved chunk a citation ID."""
    return json.dumps([
        {"id": i, "source": d.metadata["source"], "headings": d.metadata.get("headings", ""),
         "chunk_id": d.metadata.get("chunk_id", d.id), "text": d.page_content}
        for i, d in enumerate(docs, 1)
    ], ensure_ascii=False)
