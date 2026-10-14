"""Index the pinned public Temporal corpus without modifying old snapshots."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import ExperimentalMarkdownSyntaxTextSplitter, RecursiveCharacterTextSplitter

from artifacts import write_json

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus/docs"
PERSIST = ROOT / "chroma_db"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"

_FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", re.DOTALL)
_TITLE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)
_IMPORT_LINE = re.compile(r"^(?:import|export)[ \t]+(?:\{[^}]*\}[^\n]*|[^\n]*)(?:\n|$)", re.MULTILINE)
_JSX_TAG = re.compile(r"</?[A-Z][A-Za-z0-9]*(?:\s[^>]*)?/?>")
_INLINE_CODE = re.compile(r"(\x60+.*?\x60+)", re.DOTALL)
_FENCE = re.compile(r"^ {0,3}(\x60{3,}|~{3,})")


def _clean_prose(text: str) -> str:
    parts = _INLINE_CODE.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = _JSX_TAG.sub("", _IMPORT_LINE.sub("", parts[i]))
    return "".join(parts)


def clean_mdx(text: str) -> str:
    """Preserve fenced/inline code; strip frontmatter, ESM imports and JSX tags."""
    # shortcut: JSX expressions remain text; use an MDX parser if evaluating expressions becomes necessary.
    result, prose = [], []
    fence = None
    for line in _FRONTMATTER.sub("", text).splitlines(keepends=True):
        match = _FENCE.match(line)
        if fence:
            result.append(line)
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not line[match.end():].strip():
                fence = None
        elif match:
            result.append(_clean_prose("".join(prose)))
            prose.clear()
            result.append(line)
            fence = match[1]
        else:
            prose.append(line)
    result.append(_clean_prose("".join(prose)))
    return "".join(result)


def _heading_chain(meta: dict) -> str:
    return " > ".join(meta[k] for k in ("h1", "h2", "h3") if meta.get(k))


def load_chunks() -> list[Document]:
    """Read header-aware chunks while preserving code whitespace."""
    if not CORPUS.is_dir():
        raise FileNotFoundError(f"Missing corpus: {CORPUS}; run fetch_corpus.sh")
    by_header = ExperimentalMarkdownSyntaxTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")], strip_headers=False,
    )
    by_size = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=180, strip_whitespace=False,
    )
    chunks = {}
    for path in sorted(CORPUS.rglob("*.md*")):
        raw = path.read_text(encoding="utf-8")
        title_match = _TITLE.search(raw[:1000])
        title = title_match[1].strip("\"'") if title_match else path.stem
        for section in by_header.split_text(clean_mdx(raw)):
            headings = _heading_chain(section.metadata) or title
            for piece in by_size.split_documents([section]):
                if len(piece.page_content.strip()) < 50:
                    continue
                source = path.relative_to(CORPUS).as_posix()
                chunk_id = hashlib.sha256(json.dumps([source, headings, piece.page_content]).encode()).hexdigest()
                chunks[chunk_id] = Document(
                    id=chunk_id, page_content=piece.page_content,
                    metadata={"source": source, "title": title, "headings": headings,
                              "chunk_id": chunk_id, "permitted_roles": "all"},
                )
    if not chunks:
        raise ValueError(f"No usable documents in {CORPUS}")
    return list(chunks.values())


def index_spec() -> dict:
    if not CORPUS.is_dir():
        raise FileNotFoundError(f"Missing corpus: {CORPUS}")
    sources = {p.relative_to(CORPUS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(CORPUS.rglob("*.md*"))}
    if not sources:
        raise ValueError(f"Empty corpus: {CORPUS}")
    spec = {
        "sources": sources, "embedding_model": EMBED_MODEL, "embedding_revision": EMBED_REVISION,
        "pipeline": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dependencies": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
    }
    spec["fingerprint"] = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    return spec


def read_manifest() -> dict:
    path = Path(PERSIST) / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"No verified index manifest at {path}; run ingest.py")
    manifest = json.loads(path.read_text())
    if manifest["fingerprint"] != index_spec()["fingerprint"]:
        raise ValueError("Index does not match the corpus/pipeline; run ingest.py")
    return manifest


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"revision": EMBED_REVISION, "device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=4)
def _open_store(collection: str, persist: str) -> Chroma:
    return Chroma(
        collection_name=collection, embedding_function=get_embeddings(),
        persist_directory=persist, create_collection_if_not_exists=False,
    )


def get_vectorstore() -> Chroma:
    manifest = read_manifest()
    store = _open_store(manifest["collection"], str(PERSIST))
    if store._collection.count() != manifest["chunks"]:
        raise ValueError("Index is incomplete; run ingest.py")
    return store


def build_index(batch_size: int = 256) -> Chroma:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    spec = index_spec()
    chunks = load_chunks()
    collection = "temporal_docs_" + spec["fingerprint"][:24]
    store = Chroma(collection_name=collection, embedding_function=get_embeddings(), persist_directory=str(PERSIST))
    existing = set(store.get(include=[])["ids"])
    wanted = {d.id for d in chunks}
    if existing - wanted:
        raise ValueError("Unexpected documents in immutable snapshot")
    pending = [d for d in chunks if d.id not in existing]
    print(f"chunks: {len(chunks)}; already indexed: {len(existing)}", flush=True)
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        store.add_documents(batch, ids=[d.id for d in batch])
        print(f"  indexed {len(existing) + min(i + batch_size, len(pending))}/{len(chunks)}", flush=True)
    if set(store.get(include=[])["ids"]) != wanted or index_spec() != spec:
        raise ValueError("Corpus changed or indexing was incomplete; old manifest preserved")
    revision = subprocess.run(
        ["git", "-C", str(CORPUS.parent), "rev-parse", "HEAD"], capture_output=True, text=True,
    )
    write_json(Path(PERSIST) / "manifest.json", {
        **spec, "collection": collection, "chunks": len(chunks),
        "corpus_revision": revision.stdout.strip() if revision.returncode == 0 else None,
    })
    return store


if __name__ == "__main__":
    build_index()
