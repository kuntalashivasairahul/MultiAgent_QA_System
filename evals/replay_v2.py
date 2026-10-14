"""Ablate v2 gates on fixed v1 drafts; this is NOT a fresh end-to-end benchmark."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.documents import Document

import graph_v2 as v2
from artifacts import write_json
from evals.run_eval import _append, _load_partial, is_refusal
from llm import JUDGE_MODEL, MAX_RETRIES, REQUESTS_PER_SECOND

PROJECT = Path(__file__).resolve().parent.parent


def replay(baseline: Path) -> dict:
    baseline = baseline.resolve()
    records = list(_load_partial(baseline).values())
    if not records or any("answer" not in r or "correct" not in r for r in records):
        raise ValueError("Replay requires complete v1 answers and correctness judgments")
    project = PROJECT
    inputs = {"scope": "fixed-v1-draft replay; no new generation or independent correctness judging",
              "baseline": baseline.relative_to(project).as_posix(),
              "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(), "gate_model": JUDGE_MODEL,
              "max_retries": MAX_RETRIES, "requests_per_second": REQUESTS_PER_SECOND,
              "code": {p: hashlib.sha256((project / p).read_bytes()).hexdigest()
                       for p in ("graph_v2.py", "graph_v1.py", "llm.py", "retrieval.py", "state.py",
                                 "evals/replay_v2.py", "evals/run_eval.py", "uv.lock")}}
    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    output = project / "evals/results/replay_v2" / fingerprint
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "inputs.json", inputs)
    partial = output / "partial.jsonl"
    done = _load_partial(partial)
    for record in records:
        row = done.get(record["question"], {"question": record["question"]})
        docs = [Document(id=d.get("id"), page_content=d["text"], metadata=d["metadata"]) for d in record["documents"]]
        state = {"question": record["question"], "documents": docs,
                 "generation": record["answer"], "citations": record["citations"]}
        for stage, fn in (("sufficiency", v2.sufficient), ("support", v2.supported)):
            if stage in row:
                continue
            started = time.perf_counter()
            with get_usage_metadata_callback() as usage:
                try:
                    row[stage] = fn(state)[stage]
                    row.pop(stage + "_error", None)
                except Exception as exc:
                    row[stage + "_error"] = type(exc).__name__
            row[stage + "_seconds"] = time.perf_counter() - started
            row[stage + "_usage"] = usage.usage_metadata
            _append(partial, row)
        done[row["question"]] = row
        print(f"replayed: {len(done)}/{len(records)}", flush=True)
    summaries = {}
    for variant in ("v1", "sufficiency", "support", "both"):
        evaluated = []
        for record in records:
            row = done[record["question"]]
            stages = [] if variant == "v1" else (["sufficiency", "support"] if variant == "both" else [variant])
            blocked = False
            for stage in stages:
                if stage not in row:
                    break  # An error stays missing, never a successful refusal.
                if row[stage] is not None and not row[stage]["passed"]:
                    blocked = True
                    break
            if not blocked and any(stage not in row for stage in stages):
                continue
            refused = blocked or is_refusal(record["answer"])
            correct = refused if record["bucket"] == "unanswerable" else (not refused and record["correct"])
            evaluated.append((record, refused, correct))
        summaries[variant] = {"n": len(records), "scored": len(evaluated), "missing": len(records) - len(evaluated),
                              "correct_using_original_labels": sum(c for _, _, c in evaluated),
                              "answerable_refusals": sum(ref for r, ref, _ in evaluated if r["bucket"] != "unanswerable"),
                              "unanswerable_answers": sum(not ref for r, ref, _ in evaluated if r["bucket"] == "unanswerable")}
    result = {"inputs": inputs, "variants": summaries, "artifact_dir": str(output)}
    write_json(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Frozen v1 partial.jsonl")
    args = parser.parse_args()
    result = replay(args.baseline)
    print(json.dumps(result["variants"], indent=2))
    if any(v["missing"] for v in result["variants"].values()):
        raise SystemExit("Incomplete replay")
