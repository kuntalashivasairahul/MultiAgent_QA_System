"""Dense retrieval over a verified public-corpus snapshot."""
from __future__ import annotations

import json
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ingest import get_vectorstore, load_chunks

SECTION_SEED_K = 5
SECTION_MAX_CHUNKS = 10
SECTION_MAX_CHARS = 8000


@lru_cache(maxsize=8)
def _retriever(store, k: int) -> VectorStoreRetriever:
    return store.as_retriever(search_kwargs={"k": k})


def get_retriever(k: int = 5) -> VectorStoreRetriever:
    if k < 1:
        raise ValueError("k must be positive")
    return _retriever(get_vectorstore(), k)


@lru_cache(maxsize=1)
def _section_chunks(collection: str) -> dict[str, list[Document]]:
    """Collection identity invalidates canonical section membership after a rebuild."""
    sections, previous, group = {}, None, []
    for doc in load_chunks():
        key = (doc.metadata["source"], doc.metadata["headings"])
        if key != previous:
            group = []
            previous = key
        group.append(doc)
        sections[doc.id] = group
    return sections


def expand_sections(anchors: list[Document], sections: dict[str, list[Document]]) -> list[Document]:
    if any(not d.id for d in anchors):
        raise ValueError("Section anchors require stable chunk IDs")
    documents = list({d.id: d for d in anchors}.values())
    characters = sum(len(d.page_content) for d in documents)
    if len(documents) > SECTION_MAX_CHUNKS or characters > SECTION_MAX_CHARS:
        raise ValueError("Dense anchors exceed the section context budget")
    seen = {d.id for d in documents}
    for anchor in list(documents):
        if anchor.id not in sections:
            raise ValueError("Dense anchor is absent from the canonical index chunks")
        section = sections[anchor.id]
        position = next(i for i, d in enumerate(section) if d.id == anchor.id)
        for _, doc in sorted(enumerate(section), key=lambda item: (abs(item[0] - position), item[0])):
            if len(documents) == SECTION_MAX_CHUNKS:
                return documents
            if doc.id not in seen and characters + len(doc.page_content) <= SECTION_MAX_CHARS:
                documents.append(doc)
                seen.add(doc.id)
                characters += len(doc.page_content)
    return documents


def get_section_context(question: str) -> list[Document]:
    store = get_vectorstore()
    anchors = _retriever(store, SECTION_SEED_K).invoke(question)
    if not anchors:
        return []
    return expand_sections(anchors, _section_chunks(store._collection.name))

def format_docs(docs: list[Document]) -> str:
    """JSON-encode untrusted source data and give each retrieved chunk a citation ID."""
    return json.dumps([
        {"id": i, "source": d.metadata["source"], "headings": d.metadata.get("headings", ""),
         "chunk_id": d.metadata.get("chunk_id", d.id), "text": d.page_content}
        for i, d in enumerate(docs, 1)
    ], ensure_ascii=False)
