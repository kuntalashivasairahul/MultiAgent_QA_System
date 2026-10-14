"""V2 audits and ablations remain reproducible in the shared evaluator."""
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from evals import run_eval as ev
from test_evals import evaluation


def test_audits_and_usage_survive_checkpoint_and_resume(evaluation):
    module, dataset, _, _ = evaluation
    module.graph.invoke.return_value.update(
        sufficiency={"passed": True, "reason": "Evidence"},
        support={"passed": False, "reason": "Unsupported"},
        draft={"generation": "Rejected draft", "citations": []},
        generation="I don't know.", citations=[],
    )
    result = ev.run_eval(module.__name__, dataset=dataset)
    records = ev._load_partial(Path(result["artifact_dir"]) / "partial.jsonl")
    record = next(iter(records.values()))
    assert record["checks"]["draft"]["generation"] == "Rejected draft"
    assert record["generation_seconds"] >= 0
    assert record["generation_usage"] == {}  # Mock/provider without usage is not zero billed tokens.
    assert result["false_refusal_rate"] == 1 and result["supported_correct_rate"] == 0
    assert ev.run_eval(module.__name__, dataset=dataset)["run_id"] == result["run_id"]
    assert module.graph.invoke.call_count == 1


def test_variants_have_separate_checkpoints(evaluation, monkeypatch):
    module, dataset, _, _ = evaluation
    module.build_graph = Mock(return_value=module.graph)
    monkeypatch.setitem(sys.modules, "graph_v2", module)
    results = [ev.run_eval("graph_v2", dataset=dataset, variant=v) for v in ("both", "sufficiency", "support")]
    assert len({r["fingerprint"] for r in results}) == 3
    assert module.graph.invoke.call_count == 3
    assert [r["variant"] for r in results] == ["both", "sufficiency", "support"]
    assert ev.run_eval("graph_v2", dataset=dataset)["run_id"] == results[0]["run_id"]
    with pytest.raises(ValueError, match="only"):
        ev.run_eval(module.__name__, dataset=dataset, variant="support")


def test_unanswerable_unsupported_claims_are_judged_not_hidden(evaluation, monkeypatch):
    module, dataset, rows, _ = evaluation
    rows[0].update(bucket="unanswerable", answer="I don't know.", source="", evidence_groups=[])
    dataset.write_text(json.dumps(rows[0]) + "\n")
    monkeypatch.setattr(ev, "structured", lambda schema, **kwargs: Mock(
        invoke=Mock(return_value=ev.Faithfulness(grounded=False, reason="Wrong private scope"))))
    result = ev.run_eval(module.__name__, dataset=dataset)
    assert result["correctness"] == 0 and result["unsupported_answer_rate"] == 1
    assert result["faithfulness"] is None
    assert result["coverage"]["unsupported_answer_rate"] == {"eligible": 1, "scored": 1, "missing": 0}
