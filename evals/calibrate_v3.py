"""Resumable development controls against the actual v3 quality Judge."""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.documents import Document
from langchain_core.messages.ai import add_usage

import graph_v3 as v3
from artifacts import write_json
from evals.run_eval import _evaluation_lock, run_inputs

CASES = Path(__file__).with_name("v3_judge_controls.json")


def main():
    cases = json.loads(CASES.read_text())["records"]
    assert len(cases) == 17 and len({c["id"] for c in cases}) == 17
    for case in cases:
        assert type(case["expected_accept"]) is bool and case["question"].strip()
        assert case["citations"] and all(1 <= c["id"] <= len(case["documents"]) for c in case["citations"])
    metadata = run_inputs(v3, cases, CASES)
    fingerprint = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    directory = CASES.parent / "results/calibration_v3" / fingerprint
    directory.mkdir(parents=True, exist_ok=True)
    with _evaluation_lock(directory / "owner.sqlite"):
        write_json(directory / "inputs.json", metadata)
        records = []
        for case in cases:
            path = directory / (case["id"] + ".json")
            record = json.loads(path.read_text()) if path.exists() else {"id": case["id"]}
            if "verdict" not in record:
                started = time.perf_counter()
                with get_usage_metadata_callback() as usage:
                    try:
                        state = v3.initialize({"question": case["question"]})
                        state.update(documents=[Document(id=d["id"], page_content=d["text"], metadata=d["metadata"])
                                                for d in case["documents"]],
                                     generation=case["answer"], citations=case["citations"], attempt_count=1)
                        verdict = v3.judge(state)["quality"]
                        actual = v3.accepted({**state, "quality": verdict}, v3.THRESHOLD)
                        record.update(verdict=verdict, actual=actual, expected=case["expected_accept"],
                                      passed=actual is case["expected_accept"])
                        record.pop("error", None)
                        record.pop("validation_failures", None)
                    except Exception as exc:
                        record.update(error=type(exc).__name__, passed=False)
                        if hasattr(exc, "validation_failures"):
                            record["validation_failures"] = exc.validation_failures
                old, current = record.get("usage", {}), usage.usage_metadata
                record["usage"] = {model: add_usage(old.get(model), current.get(model))
                                   for model in sorted(old.keys() | current.keys())}
                record["seconds"] = record.get("seconds", 0) + time.perf_counter() - started
                write_json(path, record)
            records.append(record)
            print(case["id"], "passed=" + str(record["passed"]), flush=True)
        assert run_inputs(v3, cases, CASES) == metadata, "Control inputs changed during execution"
        result = {"scope": "Inspected development controls, not held-out accuracy or calibrated probabilities",
                  "artifact_dir": str(directory), "n": len(cases),
                  "scored": sum("verdict" in r for r in records), "passed": sum(r["passed"] for r in records),
                  "missing": sum("verdict" not in r for r in records), "records": records}
        write_json(directory / "result.json", result)
        print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
        if result["passed"] != result["n"]:
            raise SystemExit("Failed or missing Judge controls; do not promote this profile")


if __name__ == "__main__":
    main()
