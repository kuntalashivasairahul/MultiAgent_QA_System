"""Load Temporal's docs, clean them, chunk them, and index them in Chroma.

Run once: uv run python ingest.py
"""
from __future__ import annotations

import re
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

CORPUS = Path("corpus/docs")
PERSIST = "chroma_db"
COLLECTION = "temporal_docs"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_TITLE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)
_IMPORT_LINE = re.compile(r"^(?:import|export)\s+.*$", re.MULTILINE)
_JSX_TAG = re.compile(r"</?[A-Z][A-Za-z0-9]*(?:\s[^>]*)?/?>")


def clean_mdx(text: str) -> str:
    """Strip frontmatter, imports, and JSX tags — but never inside code fences.

    Splitting on ``` gives alternating prose/code segments; only even indices
    are prose. Code blocks are left untouched because Java and Rust generics
    (`List<String>`) look exactly like JSX tags to a regex.
    """
    text = _FRONTMATTER.sub("", text)
    parts = text.split("```")
    for i in range(0, len(parts), 2):
        parts[i] = _JSX_TAG.sub("", _IMPORT_LINE.sub("", parts[i]))
    return "```".join(parts)


def _heading_chain(meta: dict) -> str:
    return " > ".join(meta[k] for k in ("h1", "h2", "h3") if meta.get(k))


def load_chunks() -> list[Document]:
    """Read every markdown file into header-aware, size-bounded chunks."""
    by_header = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
        strip_headers=False,
    )
    by_size = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=180)

    chunks: list[Document] = []
    for path in sorted(CORPUS.rglob("*.md*")):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        title_match = _TITLE.search(raw[:1000])
        title = title_match.group(1) if title_match else path.stem
        body = clean_mdx(raw)
        if not body.strip():
            continue
        for section in by_header.split_text(body):
            headings = _heading_chain(section.metadata) or title
            for piece in by_size.split_documents([section]):
                if len(piece.page_content.strip()) < 50:
                    continue  # nav stubs and stray fragments retrieve as noise
                chunks.append(
                    Document(
                        page_content=piece.page_content,
                        metadata={
                            "source": str(path.relative_to(CORPUS)),
                            "title": title,
                            "headings": headings,
                            # Unenforced until v3, but retrofitting metadata
                            # after indexing means re-embedding everything.
                            "permitted_roles": "all",
                        },
                    )
                )
    return chunks


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=PERSIST,
    )


def build_index(batch_size: int = 256) -> Chroma:
    chunks = load_chunks()
    print(f"chunks: {len(chunks)}")
    store = get_vectorstore()
    for i in range(0, len(chunks), batch_size):
        store.add_documents(chunks[i : i + batch_size])
        print(f"  indexed {min(i + batch_size, len(chunks))}/{len(chunks)}", flush=True)
    return store


if __name__ == "__main__":
    build_index()
