from pathlib import Path
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

import ingest


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    monkeypatch.setattr(ingest, "CORPUS", docs)
    monkeypatch.setattr(ingest, "PERSIST", tmp_path / "index")
    monkeypatch.setattr(ingest, "get_embeddings", Mock(return_value=FakeEmbeddings()))
    return docs


def test_preserves_inline_and_both_fence_styles():
    raw = 'Use `List<String>` and ``Arc<Self>``.\n~~~java\nList<String> x;\n~~~\n'
    assert ingest.clean_mdx(raw) == raw


def test_removes_multiline_import_and_keeps_component_text():
    raw = 'import {\n  Tabs,\n} from "pkg";\n<Tabs>Use `Arc<Self>`.</Tabs>\n'
    assert ingest.clean_mdx(raw) == 'Use `Arc<Self>`.\n'


def test_final_chunks_preserve_code_indentation_and_headers(corpus):
    code = '```python\ndef hello():\n    if True:\n        return "preserve this code sample"\n```\n'
    (corpus / "sample.mdx").write_text('# Example\n\n' + code)
    chunks = ingest.load_chunks()
    assert any(code.rstrip() in d.page_content for d in chunks)
    assert all(d.metadata["headings"] == "Example" for d in chunks)


def test_rebuild_is_idempotent_and_publishes_new_snapshot(corpus):
    first = corpus / "first.mdx"
    first.write_text('# First\n\n' + 'Initial documentation text. ' * 8)
    store = ingest.build_index()
    ids = store.get()["ids"]
    assert ingest.build_index().get()["ids"] == ids
    first.unlink()
    (corpus / "second.mdx").write_text('# Second\n\n' + 'Replacement documentation text. ' * 8)
    replacement = ingest.build_index()
    assert {m["source"] for m in replacement.get()["metadatas"]} == {"second.mdx"}
    assert store.get()["ids"] == ids  # A failed/new build must not destroy the old snapshot.


def test_missing_or_empty_corpus_and_unbuilt_index_fail(corpus):
    with pytest.raises((ValueError, FileNotFoundError)):
        ingest.build_index()
    with pytest.raises((ValueError, FileNotFoundError)):
        ingest.get_vectorstore()


def test_failed_build_keeps_previous_manifest(corpus, monkeypatch):
    source = corpus / "sample.mdx"
    source.write_text('# First\n\n' + 'Initial documentation text. ' * 8)
    ingest.build_index()
    manifest = (ingest.PERSIST / "manifest.json").read_bytes()
    source.write_text('# Second\n\n' + 'Changed documentation text. ' * 8)
    monkeypatch.setattr(ingest.get_embeddings(), "embed_documents", Mock(side_effect=RuntimeError("failed embedding")))
    with pytest.raises(RuntimeError, match="failed embedding"):
        ingest.build_index()
    assert (ingest.PERSIST / "manifest.json").read_bytes() == manifest


@pytest.mark.integration
def test_project_paths_work_from_another_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ingest.CORPUS.is_absolute() and Path(ingest.PERSIST).is_absolute()
    assert ingest.read_manifest()["chunks"] > 0


def test_same_id_content_corruption_is_rejected_on_rebuild_and_read(corpus):
    (corpus / "first.mdx").write_text('# First\n\n' + 'Canonical source text. ' * 8)
    store = ingest.build_index()
    original = store.get()
    store.update_documents(ids=[original["ids"][0]], documents=[Document(
        page_content="Corrupted content with the same ID", metadata=original["metadatas"][0])])
    with pytest.raises(ValueError, match="canonical|integrity"):
        ingest.build_index()
    with pytest.raises(ValueError, match="canonical|integrity"):
        ingest.get_vectorstore()
