"""Replay errors remain missing and paid checks resume independently."""
import json

from evals import replay_v2 as replay


def test_replay_ablation_and_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "PROJECT", tmp_path)
    for name in ("graph_v2.py", "graph_v1.py", "llm.py", "retrieval.py", "state.py", "uv.lock",
                 "evals/replay_v2.py", "evals/run_eval.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture code")
    baseline = tmp_path / "baseline.jsonl"
    records = [{"question": q, "bucket": bucket, "answer": "Wrong private answer" if bucket == "unanswerable" else "Known fact",
                "correct": bucket != "unanswerable", "citations": [], "documents": []}
               for q, bucket in (("Known?", "direct"), ("Private?", "unanswerable"))]
    baseline.write_text("".join(json.dumps(r) + "\n" for r in records))
    calls = []
    def sufficient(state):
        calls.append(state["question"])
        if state["question"] == "Known?":
            raise RuntimeError("Outage")
        return {"sufficiency": {"passed": False}}
    monkeypatch.setattr(replay.v2, "sufficient", sufficient)
    monkeypatch.setattr(replay.v2, "supported", lambda s: {"support": {"passed": s["question"] == "Known?"}})
    first = replay.replay(baseline)
    assert first["variants"]["both"]["missing"] == 1
    assert first["variants"]["support"]["correct_using_original_labels"] == 2
    monkeypatch.setattr(replay.v2, "sufficient", lambda s: {"sufficiency": {"passed": True}})
    second = replay.replay(baseline)
    assert second["variants"]["both"]["missing"] == 0
    assert second["variants"]["both"]["correct_using_original_labels"] == 2
    assert second["variants"]["sufficiency"]["unanswerable_answers"] == 0
    assert second["variants"]["v1"]["unanswerable_answers"] == 1
    assert len(calls) == 2
