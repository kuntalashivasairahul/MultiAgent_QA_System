"""Bounded section context, version wiring, and the real short-command regression."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

import retrieval as r


def doc(name, text=None, *, source="guide.mdx", heading="Step"):
    return Document(id=name, page_content=text or name,
                    metadata={"chunk_id": name, "source": source, "headings": heading})


def test_expansion_keeps_anchors_then_nearest_neighbors_without_duplicates():
    left, anchor, right, other = [doc(n) for n in ("left", "anchor", "right", "other")]
    group = [left, anchor, right]
    sections = {d.id: group for d in group}
    sections[other.id] = [other]
    anchors = [anchor, other, anchor]
    out = r.expand_sections(anchors, sections)
    assert [d.id for d in out] == ["anchor", "other", "left", "right"]
    assert anchors == [anchor, other, anchor]


def test_chunk_budget_preserves_anchors(monkeypatch):
    monkeypatch.setattr(r, "SECTION_MAX_CHUNKS", 3)
    a, b, c, other = [doc(n) for n in ("a", "b", "c", "other")]
    sections = {d.id: [a, b, c] for d in (a, b, c)}
    sections[other.id] = [other]
    assert r.expand_sections([a, other], sections) == [a, other, b]


def test_character_budget_skips_large_neighbors_without_truncating(monkeypatch):
    monkeypatch.setattr(r, "SECTION_MAX_CHARS", 8)
    a, large, small = doc("a"), doc("large", "x" * 20), doc("small", "tail")
    out = r.expand_sections([a], {d.id: [a, large, small] for d in (a, large, small)})
    assert out == [a, small] and sum(len(d.page_content) for d in out) <= 8
    assert large.page_content == "x" * 20


def test_oversized_anchors_fail_instead_of_silently_losing_evidence(monkeypatch):
    monkeypatch.setattr(r, "SECTION_MAX_CHARS", 2)
    a = doc("a", "long anchor")
    with pytest.raises(ValueError, match="anchors.*budget"):
        r.expand_sections([a], {a.id: [a]})


def test_unknown_anchor_fails_clearly():
    with pytest.raises(ValueError, match="canonical"):
        r.expand_sections([doc("unknown")], {})


def test_section_membership_uses_contiguous_source_and_heading_runs_and_snapshot_cache(monkeypatch):
    a, b = doc("a"), doc("b")
    boundary = doc("boundary", heading="Other")
    repeated = doc("repeated")
    other_source = doc("other-source", source="other.mdx")
    loader = Mock(return_value=[a, b, boundary, repeated, other_source])
    monkeypatch.setattr(r, "load_chunks", loader)
    r._section_chunks.cache_clear()
    try:
        sections = r._section_chunks("snapshot-a")
        assert sections[a.id] == sections[b.id] == [a, b]
        assert sections[repeated.id] == [repeated]
        assert sections[other_source.id] == [other_source]
        assert r._section_chunks("snapshot-a") is sections and loader.call_count == 1
        r._section_chunks("snapshot-b")
        assert loader.call_count == 2
    finally:
        r._section_chunks.cache_clear()


def test_empty_retrieval_avoids_section_loading(monkeypatch):
    monkeypatch.setattr(r, "get_vectorstore", lambda: SimpleNamespace(_collection=SimpleNamespace(name="test")))
    monkeypatch.setattr(r, "_retriever", lambda store, k: SimpleNamespace(invoke=lambda question: []))
    loader = Mock(side_effect=AssertionError("No anchors need no expansion"))
    monkeypatch.setattr(r, "_section_chunks", loader)
    assert r.get_section_context("Unknown?") == []
    loader.assert_not_called()


def test_v21_graph_generates_and_cites_added_evidence(monkeypatch):
    import graph_v1
    import graph_v2 as v2
    import graph_v2_1 as v21
    anchors = [doc("intro", "Start the Worker with this command:")]
    command = doc("command", "```bash\npython worker.py\n```")
    retrieve = Mock(return_value=anchors + [command])
    monkeypatch.setattr(v21, "get_section_context", retrieve)
    generator = Mock(return_value=graph_v1.GroundedAnswer(answer="python worker.py", citations=[2]))
    monkeypatch.setattr(graph_v1, "structured", lambda schema: SimpleNamespace(invoke=generator))
    verdict = v2.EvidenceCheck(passed=True, reason="The command is explicit.",
                               quotes=[v2.Quote(id=2, text="python worker.py")])
    grader = Mock(return_value=verdict)
    monkeypatch.setattr(v2, "structured", lambda *a, **kw: SimpleNamespace(invoke=grader))
    out = v21.graph.invoke({"question": "How do I start this Worker?", "draft": {"stale": True}})
    assert out["generation"] == "python worker.py" and out["draft"] is None
    assert out["citations"] == [{"id": 2, "source": "guide.mdx", "chunk_id": "command"}]
    assert grader.call_count == 2 and generator.call_count == 1
    retrieve.assert_called_once_with("How do I start this Worker?")


def test_v21_insufficient_evidence_does_not_generate(monkeypatch):
    import graph_v1
    import graph_v2 as v2
    import graph_v2_1 as v21
    monkeypatch.setattr(v21, "get_section_context", lambda question: [doc("sample")])
    generator = Mock(side_effect=AssertionError("Do not generate private facts"))
    monkeypatch.setattr(graph_v1, "structured", generator)
    monkeypatch.setattr(v2, "structured", lambda *a, **kw: SimpleNamespace(invoke=lambda messages:
        v2.EvidenceCheck(passed=False, reason="Private scope is absent.", quotes=[])))
    out = v21.graph.invoke({"question": "What is our private production setting?"})
    assert out["generation"] == v2.REFUSAL and out["citations"] == [] and out["support"] is None
    generator.assert_not_called()


def test_v21_rejects_bad_question_before_retrieval(monkeypatch):
    import graph_v2_1 as v21
    retrieve = Mock()
    monkeypatch.setattr(v21, "get_section_context", retrieve)
    with pytest.raises(ValueError, match="non-empty"):
        v21.graph.invoke({"question": ""})
    retrieve.assert_not_called()


@pytest.mark.integration
def test_real_section_expansion_recovers_worker_command_and_keeps_dense_anchors():
    question = "In the Celery-to-Standalone-Activity migration guide, what command starts the Python Worker?"
    anchors = r.get_retriever().invoke(question)
    expanded = r.get_section_context(question)
    assert [d.id for d in expanded[:len(anchors)]] == [d.id for d in anchors]
    assert not any("python worker.py" in d.page_content for d in anchors)
    assert any("python worker.py" in d.page_content for d in expanded)
    assert len(expanded) <= r.SECTION_MAX_CHUNKS
    assert sum(len(d.page_content) for d in expanded) <= r.SECTION_MAX_CHARS


def test_context_limits_are_fingerprinted_as_a_snapshot(tmp_path, monkeypatch):
    from evals import run_eval as ev
    dataset = tmp_path / "test.jsonl"
    dataset.write_text("{}\n")
    monkeypatch.setattr(ev, "read_manifest", lambda: {"fingerprint": "test"})
    module = SimpleNamespace(__name__="graph_v2_1", USES_RETRIEVAL=True, RETRIEVAL_K=10,
                             CONTEXT_LIMITS={"seed_k": 5, "max_chunks": 10})
    before = ev.run_inputs(module, [], dataset)
    module.CONTEXT_LIMITS["max_chunks"] = 11
    after = ev.run_inputs(module, [], dataset)
    assert before["context_limits"]["max_chunks"] == 10 and before != after


def test_index_errors_propagate_instead_of_becoming_refusals(monkeypatch):
    monkeypatch.setattr(r, "get_vectorstore", Mock(side_effect=ValueError("Index does not match")))
    with pytest.raises(ValueError, match="Index does not match"):
        r.get_section_context("Question?")


def test_missing_chunk_ids_fail_clearly():
    with pytest.raises(ValueError, match="stable chunk IDs"):
        r.expand_sections([Document(page_content="No stable identity")], {})


def test_returned_context_cannot_mutate_cached_section_evidence():
    anchor, neighbor = doc("anchor"), doc("neighbor", "Original source evidence")
    sections = {d.id: [anchor, neighbor] for d in (anchor, neighbor)}
    first = r.expand_sections([anchor], sections)
    first[1].page_content = "Untrusted replacement"
    first[1].metadata["headings"] = "Wrong heading"
    second = r.expand_sections([anchor], sections)
    assert second[1].page_content == "Original source evidence"
    assert second[1].metadata["headings"] == "Step"
