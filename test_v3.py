"""Behavioral contracts for the three-role graph and its bounded semantic retry."""
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import ValidationError

import graph_v1
import graph_v3 as v3
from graph_v2 import REFUSAL


def verdict(score=1.0, passed=True, *, retry=False):
    return v3.QualityVerdict(passed=passed, confidence=score, reason="Fixture quality assessment.",
                            quotes=[{"id": 1, "text": "Part B." if retry else "Part A."}],
                            retry_query="Part B")


def controlled(monkeypatch, qualities):
    searches, generations = [], []
    documents = [Document(id="old", page_content="Part A.", metadata={"source": "a.mdx", "chunk_id": "old"}),
                 Document(id="new", page_content="Part B.", metadata={"source": "b.mdx", "chunk_id": "new"})]

    def retrieve(query, *, exclude_ids=()):
        searches.append((query, exclude_ids))
        return [documents[1 if exclude_ids else 0]]

    outputs = iter(qualities)

    def structured(schema, *, judge=False):
        def invoke(messages):
            if judge:
                result = next(outputs)
                if isinstance(result, Exception):
                    raise result
                return result
            generations.append(messages)
            return graph_v1.GroundedAnswer(answer="Part A." if len(generations) == 1 else "Part B.", citations=[1])
        return SimpleNamespace(invoke=invoke)

    monkeypatch.setattr(v3, "get_hybrid_context", retrieve)
    monkeypatch.setattr(v3.v3_llm, "structured", structured)
    return searches, generations


def test_low_quality_retrieves_new_evidence_and_preserves_both_attempts(monkeypatch):
    searches, generations = controlled(monkeypatch, [verdict(0.4), verdict(retry=True)])
    result = v3.build_graph().invoke({"question": "Explain both parts."})
    assert len(searches) == len(generations) == result["attempt_count"] == 2
    assert searches[0] == ("Explain both parts.", ())
    assert "Part B" in searches[1][0] and searches[1][1] == ("old",)
    assert result["generation"] == "Part B." and result["citations"][0]["chunk_id"] == "new"
    assert result["history"][0]["documents"][0]["id"] == "old"
    assert result["history"][1]["new_document_ids"] == ["new"]
    assert [d.id for d in result["documents"]] == ["new", "old"]


def test_high_quality_terminates_without_retry_and_resets_supplied_history(monkeypatch):
    searches, _ = controlled(monkeypatch, [verdict(0.8)])
    result = v3.graph.invoke({"question": " Explain A. ", "attempt_count": 99, "history": [{"fake": True}]})
    assert result["generation"] == "Part A." and result["attempt_count"] == 1
    assert len(searches) == len(result["history"]) == 1
    assert result["question"] == "Explain A."


@pytest.mark.parametrize("quality", [verdict(0.1), verdict(1.0, passed=False)])
def test_low_quality_or_semantic_failure_cannot_escape_retry_bound(monkeypatch, quality):
    second = quality.model_copy(update={"quotes": [v3.graph_v2.Quote(id=1, text="Part B.")]})
    searches, _ = controlled(monkeypatch, [quality, second])
    result = v3.graph.invoke({"question": "Explain A."})
    assert len(searches) == 2 and result["generation"] == REFUSAL and not result["citations"]
    assert result["draft"]["generation"] == "Part B." and len(result["history"]) == 2


def test_empty_context_refuses_without_model_calls(monkeypatch):
    monkeypatch.setattr(v3, "get_hybrid_context", lambda *a, **k: [])
    monkeypatch.setattr(v3.v3_llm, "structured", lambda *a, **k: pytest.fail("No evidence must not call model"))
    result = v3.graph.invoke({"question": "Private unknown fact?"})
    assert result["generation"] == REFUSAL and result["attempt_count"] == 2


def test_operational_failure_resumes_without_repeating_retrieval_or_reasoning(monkeypatch, tmp_path):
    searches, generations = controlled(monkeypatch, [RuntimeError("provider unavailable"), verdict()])
    config = {"configurable": {"thread_id": "independent-request"}}
    path = str(tmp_path / "graph.sqlite")
    with SqliteSaver.from_conn_string(path) as saver:
        graph = v3.build_graph(checkpointer=saver)
        with pytest.raises(RuntimeError):
            graph.invoke({"question": "Explain A."}, config, durability="sync")
    with SqliteSaver.from_conn_string(path) as saver:
        result = v3.build_graph(checkpointer=saver).invoke(None, config, durability="sync")
    assert result["generation"] == "Part A."
    assert len(searches) == len(generations) == 1


def test_fabricated_quote_is_error_not_semantic_refusal(monkeypatch):
    bad = verdict().model_copy(update={"quotes": [v3.graph_v2.Quote(id=1, text="Invented evidence.")]})
    controlled(monkeypatch, [bad, bad, bad])
    with pytest.raises(ValueError, match="non-verbatim") as error:
        v3.graph.invoke({"question": "Explain A."})
    assert len(error.value.validation_failures) == 3


@pytest.mark.parametrize("threshold", [0, -1, 1.1, float("nan"), float("inf"), True])
def test_invalid_threshold_rejected(threshold):
    with pytest.raises(ValueError):
        v3.build_graph(threshold=threshold)


@pytest.mark.parametrize("score", [-0.1, 1.1, float("nan"), float("inf"), True])
def test_invalid_score_rejected(score):
    with pytest.raises(ValidationError):
        verdict(score)


@pytest.mark.integration
def test_real_retry_excludes_seen_chunks_and_obeys_context_limits():
    from retrieval import get_hybrid_context
    first = get_hybrid_context("What is a Local Activity in Temporal?")
    assert first
    seen = tuple(d.id for d in first)
    second = get_hybrid_context("Local Activity short-lived operations and retries", exclude_ids=seen)
    assert second and not {d.id for d in second}.intersection(seen)
    assert len(second) <= 12 and sum(len(d.page_content) for d in second) <= 8000
