import json
import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from evals import run_eval as ev


@pytest.fixture
def evaluation(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("a.mdx", "b.mdx", "alternative.mdx"):
        (docs / name).write_text("Test evidence")
    monkeypatch.setattr(ev, "CORPUS", docs, raising=False)
    monkeypatch.setattr(ev, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(ev, "run_inputs", lambda module, rows, dataset: {"rows": rows, "model": "fake"}, raising=False)
    module = types.ModuleType("graph_v99")
    module.USES_RETRIEVAL = True
    module.RETRIEVAL_K = 5
    module.graph = Mock()
    module.graph.invoke.return_value = {
        "generation": "Supported answer", "citations": [],
        "documents": [Document(page_content="Evidence A", metadata={"source": "a.mdx"})],
    }
    monkeypatch.setitem(sys.modules, module.__name__, module)
    chains = []
    def structured(schema, **kwargs):
        chain = Mock()
        chain.invoke.return_value = schema(**({"correct": True} if schema is ev.Correctness else {"grounded": True}), reason="Test verdict")
        chains.append(chain)
        return chain
    monkeypatch.setattr(ev, "structured", structured)
    dataset = tmp_path / "golden.jsonl"
    rows = [{"question": "Specific question?", "answer": "Supported answer", "bucket": "multihop",
             "source": "a.mdx,b.mdx", "evidence_groups": [["a.mdx", "alternative.mdx"], ["b.mdx"]]}]
    dataset.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return module, dataset, rows, chains


def test_refusal_requires_whole_answer():
    assert ev.is_refusal(" I don’t know.\n")
    assert not ev.is_refusal("I don't know for sure, but the price is $999.")
    assert not ev.is_refusal("The provided context does not contain that information.")


def test_torn_checkpoint_recovers_but_internal_corruption_fails(tmp_path):
    path = tmp_path / "partial.jsonl"
    path.write_text('{"question":"Q"}\n{"question":')
    assert ev._load_partial(path) == {"Q": {"question": "Q"}}
    assert path.read_text() == '{"question":"Q"}\n'
    path.write_text('broken\n{"question":"Q"}\n')
    with pytest.raises(ValueError):
        ev._load_partial(path)


def test_source_recall_counts_every_group_and_accepts_alternatives():
    row = {"evidence_groups": [["a.mdx", "alternative.mdx"], ["b.mdx"]]}
    assert ev.source_recall(row, [{"metadata": {"source": "alternative.mdx"}}]) == 0.5
    assert ev.source_recall(row, []) == 0.0


def test_run_preserves_evidence_and_scores_partial_retrieval(evaluation):
    module, dataset, rows, chains = evaluation
    result = ev.run_eval(module.__name__, dataset=dataset)
    assert result["recall_at_k"] == 0.5
    assert result["all_sources_rate"] == 0.0
    records = ev._load_partial(Path(result["artifact_dir"]) / "partial.jsonl")
    rec = records[rows[0]["question"]]
    assert rec["answer"] == "Supported answer"
    assert rec["documents"][0]["metadata"]["source"] == "a.mdx"
    assert rec["judges"]["correct"]["output"]["reason"] == "Test verdict"
    messages = chains[0].invoke.call_args.args[0]
    assert messages[0].type == "system" and rows[0]["question"] in messages[1].content


def test_same_inputs_resume_changed_reference_and_fresh_rerun(evaluation):
    module, dataset, rows, _ = evaluation
    first = ev.run_eval(module.__name__, dataset=dataset)
    assert ev.run_eval(module.__name__, dataset=dataset)["run_id"] == first["run_id"]
    assert module.graph.invoke.call_count == 1
    rows[0]["answer"] = "Changed reference"
    dataset.write_text(json.dumps(rows[0]) + "\n")
    changed = ev.run_eval(module.__name__, dataset=dataset)
    assert changed["fingerprint"] != first["fingerprint"]
    assert module.graph.invoke.call_count == 2
    assert ev.run_eval(module.__name__, dataset=dataset, fresh=True)["run_id"] != changed["run_id"]
    assert module.graph.invoke.call_count == 3


def test_empty_retrieval_is_a_miss(evaluation):
    module, dataset, _, _ = evaluation
    module.graph.invoke.return_value = {"generation": "I don't know.", "documents": [], "citations": []}
    result = ev.run_eval(module.__name__, dataset=dataset)
    assert result["recall_at_k"] == 0.0
    assert result["coverage"]["recall_at_k"] == {"eligible": 1, "scored": 1, "missing": 0}


def test_judge_failure_is_visible_and_retries_without_regeneration(evaluation, monkeypatch):
    module, dataset, _, _ = evaluation
    failed = Mock()
    failed.invoke.side_effect = ValueError("simulated parse failure")
    ok = Mock()
    ok.invoke.return_value = ev.Correctness(correct=True, reason="Matches")
    monkeypatch.setattr(ev, "structured", lambda schema, **kwargs: ok if schema is ev.Correctness else failed)
    first = ev.run_eval(module.__name__, dataset=dataset)
    assert first["coverage"]["faithfulness"]["missing"] == 1
    assert first["unjudged"] == 1 and first["status"] == "incomplete"
    failed.invoke.side_effect = None
    failed.invoke.return_value = ev.Faithfulness(grounded=True, reason="Supported")
    second = ev.run_eval(module.__name__, dataset=dataset)
    assert second["unjudged"] == 0 and second["status"] == "complete"
    assert module.graph.invoke.call_count == 1


def test_limited_runs_never_overwrite_full_result(evaluation):
    module, dataset, rows, _ = evaluation
    rows.append({**rows[0], "question": "Second question?"})
    dataset.write_text("".join(json.dumps(r) + "\n" for r in rows))
    full = ev.run_eval(module.__name__, dataset=dataset)
    sample = ev.run_eval(module.__name__, limit=1, dataset=dataset)
    assert full["artifact_dir"] != sample["artifact_dir"]
    assert sample["scope"] == "sample"
    assert json.loads((Path(full["artifact_dir"]) / "result.json").read_text())["n"] == 2


def test_dataset_validation_rejects_duplicates_and_path_escape(evaluation):
    _, dataset, rows, _ = evaluation
    dataset.write_text(json.dumps(rows[0]) + "\n" + json.dumps(rows[0]) + "\n")
    with pytest.raises(ValueError, match="duplicate"):
        ev.load_golden(dataset=dataset)
    rows[0]["evidence_groups"] = [["../outside.mdx"]]
    dataset.write_text(json.dumps(rows[0]) + "\n")
    with pytest.raises(ValueError):
        ev.load_golden(dataset=dataset)


def test_generation_failure_stays_missing_and_resume_only_retries_failed_row(evaluation):
    module, dataset, rows, _ = evaluation
    rows.append({**rows[0], "question": "Second question?"})
    dataset.write_text("".join(json.dumps(r) + "\n" for r in rows))
    answer = module.graph.invoke.return_value
    module.graph.invoke.side_effect = [answer, RuntimeError("Temporary provider limit")]
    failed = ev.run_eval(module.__name__, dataset=dataset)
    assert failed["status"] == "incomplete" and failed["generation_errors"] == 1
    assert failed["coverage"]["correctness"] == {"eligible": 2, "scored": 1, "missing": 1}
    module.graph.invoke.side_effect = None
    recovered = ev.run_eval(module.__name__, dataset=dataset)
    assert recovered["status"] == "complete" and recovered["generation_errors"] == 0
    assert module.graph.invoke.call_count == 3
