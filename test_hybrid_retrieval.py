"""Selection contracts and frozen development facts; no paid model calls."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

import retrieval as r


def fixture_index(monkeypatch, chunks):
    store = SimpleNamespace(_collection=SimpleNamespace(name="fixture"),
                            similarity_search=Mock(return_value=chunks))
    monkeypatch.setattr(r, "get_vectorstore", lambda: store)
    monkeypatch.setattr(r, "load_chunks", lambda: chunks)
    r._lexical_index.cache_clear()
    r._section_chunks.cache_clear()
    return store


def chunk(identifier, text, source="guide.mdx", heading="Guide"):
    return Document(id=identifier, page_content=text,
                    metadata={"source": source, "headings": heading, "chunk_id": identifier})


def test_hybrid_budgets_deduplication_and_copy_isolation(monkeypatch):
    chunks = [chunk(str(i), "workflow " * 90) for i in range(20)]
    fixture_index(monkeypatch, chunks)
    out = r.get_hybrid_context("workflow")
    assert len(out) <= 12 and len({d.id for d in out}) == len(out)
    assert sum(len(d.page_content) for d in out) <= 8000
    out[0].metadata["source"] = "mutated"
    out[0].page_content = "mutated"
    assert all(d.metadata["source"] == "guide.mdx" for d in r.get_hybrid_context("workflow"))
    assert all(d.page_content != "mutated" for d in chunks)


def test_sdk_pools_balance_and_do_not_treat_go_to_as_language(monkeypatch):
    chunks = [chunk("j", "Java workflow", "develop/java/workflows/a.mdx"),
              chunk("p", "Python workflow", "develop/python/workflows/a.mdx")]
    store = fixture_index(monkeypatch, chunks)
    out = r.get_hybrid_context("Java and Python workflow")
    assert {d.id for d in out} == {"j", "p"}
    assert [call.kwargs.get("filter") for call in store.similarity_search.call_args_list][1:] == [
        {"source": {"$in": ["develop/java/workflows/a.mdx"]}},
        {"source": {"$in": ["develop/python/workflows/a.mdx"]}}]
    store.similarity_search.reset_mock()
    r.get_hybrid_context("Go to the dashboard")
    assert store.similarity_search.call_count == 1


def test_missing_sdk_and_no_lexical_overlap_use_dense_fallback(monkeypatch):
    d = chunk("a", "workflow execution")
    store = fixture_index(monkeypatch, [d])
    assert r.get_hybrid_context("Python xyzzy") == [d]
    assert store.similarity_search.call_count == 1


def test_unknown_dense_id_and_index_errors_propagate(monkeypatch):
    store = fixture_index(monkeypatch, [chunk("a", "workflow")])
    store.similarity_search.return_value = [chunk("missing", "workflow")]
    with pytest.raises(ValueError, match="canonical"):
        r.get_hybrid_context("workflow")
    store.similarity_search.side_effect = RuntimeError("index unavailable")
    with pytest.raises(RuntimeError, match="index unavailable"):
        r.get_hybrid_context("workflow")


def test_fusion_ties_are_stable_and_duplicates_share_one_ranked_id():
    assert r._fuse(["b", "a"], ["a", "b"]) == ["b", "a"]
    assert r._fuse([], ["z", "a"]) == ["z", "a"]


@pytest.mark.integration
def test_frozen_development_facts_are_in_actual_v21_context():
    import graph_v2_1 as v21
    # Clear fixture caches left by unit tests before using the real snapshot.
    r._lexical_index.cache_clear()
    r._section_chunks.cache_clear()
    rows = json.loads((Path(__file__).parent / "evals/retrieval_labels_v2.json").read_text())["records"]
    hits, complete = 0, 0
    for row in rows:
        docs = v21.retrieve({"question": row["question"]})["documents"]
        found = [any(d.metadata["source"] == fact["source"] and fact["quote"] in d.page_content
                     for d in docs) for fact in row["facts"]]
        hits += sum(found)
        complete += all(found)
    assert hits >= 10 and complete >= 6
