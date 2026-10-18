"""Native-control recovery retains a completed cited-support assessment."""
import json
from types import SimpleNamespace

import pytest

from evals import calibrate_v3
import graph_v3 as v3


def test_control_resumption_does_not_repeat_completed_cited_support(monkeypatch, tmp_path):
    cases = [{"id": f"case-{i}", "question": f"Question {i}", "answer": "Part A.",
              "documents": [{"id": "a", "text": "Part A.", "metadata": {"source": "a.mdx"}}],
              "citations": [{"id": 1}], "expected_accept": True} for i in range(17)]
    fixture = tmp_path / "controls.json"
    fixture.write_text(json.dumps({"records": cases}))
    monkeypatch.setattr(calibrate_v3, "CASES", fixture)
    monkeypatch.setattr(calibrate_v3, "run_inputs", lambda *a: {"test": "context-recovery"})
    calls = []

    def invoke(messages):
        stage = "context" if "background_documents" in json.loads(messages[1].content) else "cited_support"
        calls.append(stage)
        if stage == "context" and calls.count("context") == 1:
            raise RuntimeError("Provider unavailable")
        return v3.QualityVerdict(passed=True, confidence=1.0, reason="Supported.",
                                 quotes=[{"id": 1, "text": "Part A."}], retry_query="")

    monkeypatch.setattr(v3.v3_llm, "structured", lambda *a, **kw: SimpleNamespace(invoke=invoke))
    with pytest.raises(SystemExit, match="Failed or missing"):
        calibrate_v3.main()
    first = next(tmp_path.glob("results/calibration_v3/*/case-0.json"))
    assert json.loads(first.read_text())["cited_support"]["passed"] is True
    calibrate_v3.main()
    assert calls.count("cited_support") == 17
    assert calls.count("context") == 18
