"""Dense retrieval over a verified public-corpus snapshot."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from itertools import zip_longest

from sklearn.feature_extraction.text import TfidfVectorizer

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
                documents.append(doc.model_copy(deep=True))
                seen.add(doc.id)
                characters += len(doc.page_content)
    return documents


def get_section_context(question: str) -> list[Document]:
    store = get_vectorstore()
    anchors = _retriever(store, SECTION_SEED_K).invoke(question)
    if not anchors:
        return []
    return expand_sections(anchors, _section_chunks(store._collection.name))

HYBRID_LIMITS = {"dense_candidates": 100, "sdk_dense_candidates": 20, "lexical_candidates": 100,
                 "lexical_weight": 2, "rrf_constant": 60, "sdk_reserve": 2, "anchors": 6,
                 "max_chunks": 12, "max_document_text_characters": 8000}
SDK_PATTERNS = {"go": r"\bGo\b(?!\s+to\b)|(?i:\bin\s+go\b|\bgo\s+sdk\b)",
                **{sdk: rf"(?i:\b{sdk}\b)" for sdk in
                   ("python", "java", "typescript", "php", "rust", "ruby")},
                "dotnet": r"(?i:\.net\b|\bdotnet\b|(?<!\w)c#(?!\w))"}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text).lower())


@lru_cache(maxsize=1)
def _lexical_index(collection: str):
    chunks = load_chunks()
    vectorizer = TfidfVectorizer(sublinear_tf=True, stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([
        _normalize(d.metadata["source"] + " " + d.metadata["headings"] + " " + d.page_content)
        for d in chunks])
    return chunks, vectorizer, matrix


def _fuse(lexical: list[str], dense: list[str]) -> list[str]:
    scores = {}
    for weight, identifiers in ((HYBRID_LIMITS["lexical_weight"], lexical), (1, dense)):
        for rank, identifier in enumerate(identifiers, 1):
            scores[identifier] = scores.get(identifier, 0) + weight / (HYBRID_LIMITS["rrf_constant"] + rank)
    return sorted(scores, key=lambda identifier: (-scores[identifier], identifier))


def get_hybrid_context(question: str) -> list[Document]:
    store = get_vectorstore()
    chunks, vectorizer, matrix = _lexical_index(store._collection.name)
    by_id = {d.id: d for d in chunks}
    scores = (matrix @ vectorizer.transform([_normalize(question)]).T).toarray().ravel()
    lexical = [chunks[i] for i in sorted(range(len(chunks)), key=lambda i: (-scores[i], chunks[i].id))
               if scores[i] > 0]
    pools = [_fuse([d.id for d in lexical[:HYBRID_LIMITS["lexical_candidates"]]],
                   [d.id for d in store.similarity_search(question, k=HYBRID_LIMITS["dense_candidates"])])]
    sdks = sorted((match.start(), sdk) for sdk, pattern in SDK_PATTERNS.items()
                  if (match := re.search(pattern, question)))
    for _, sdk in sdks:
        sources = sorted({d.metadata["source"] for d in chunks
                          if d.metadata["source"].startswith("develop/" + sdk + "/")})
        if sources:
            pools.append(_fuse(
                [d.id for d in lexical if d.metadata["source"] in sources][:HYBRID_LIMITS["lexical_candidates"]],
                [d.id for d in store.similarity_search(question, k=HYBRID_LIMITS["sdk_dense_candidates"],
                                                      filter={"source": {"$in": sources}})]))
    selected, used, characters = [], set(), 0

    def add(identifier):
        nonlocal characters
        if identifier not in by_id:
            raise ValueError("Retrieved ID is absent from the canonical index chunks")
        doc = by_id[identifier]
        if identifier in used or len(selected) == HYBRID_LIMITS["max_chunks"]:
            return False
        if characters + len(doc.page_content) > HYBRID_LIMITS["max_document_text_characters"]:
            return False
        selected.append(doc)
        used.add(identifier)
        characters += len(doc.page_content)
        return True

    sdk_pools = [iter(pool) for pool in pools[1:]]
    for _ in range(HYBRID_LIMITS["sdk_reserve"]):
        for candidates in sdk_pools:
            if len(selected) < HYBRID_LIMITS["anchors"]:
                for identifier in candidates:
                    if add(identifier):
                        break
    for identifier in pools[0]:
        if len(selected) == HYBRID_LIMITS["anchors"]:
            break
        add(identifier)
    sections = _section_chunks(store._collection.name)
    neighbors = []
    for anchor in selected:
        section = sections[anchor.id]
        position = next(i for i, d in enumerate(section) if d.id == anchor.id)
        neighbors.append([d.id for i, d in sorted(enumerate(section),
                          key=lambda item: (abs(item[0] - position), item[0])) if d.id not in used])
    for group in zip_longest(*neighbors):
        for identifier in group:
            if identifier is not None:
                add(identifier)
        if len(selected) == HYBRID_LIMITS["max_chunks"]:
            break
    for identifier in pools[0]:
        if len(selected) == HYBRID_LIMITS["max_chunks"]:
            break
        add(identifier)
    return [d.model_copy(deep=True) for d in selected]


def format_docs(docs: list[Document]) -> str:
    """JSON-encode untrusted source data and give each retrieved chunk a citation ID."""
    return json.dumps([
        {"id": i, "source": d.metadata["source"], "headings": d.metadata.get("headings", ""),
         "chunk_id": d.metadata.get("chunk_id", d.id), "text": d.page_content}
        for i, d in enumerate(docs, 1)
    ], ensure_ascii=False)
