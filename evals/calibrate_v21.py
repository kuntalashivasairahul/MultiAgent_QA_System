"""Versioned, resumable native controls for both gates and evaluation judges."""
import hashlib
import inspect
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.documents import Document
from langchain_core.messages.ai import add_usage

import graph_v2 as v2
import llm
from artifacts import write_json
from evals.calibrate import CASES as JUDGE_CASES
from evals.calibrate_v2 import CASES as GATE_CASES
from evals.run_eval import Correctness, Faithfulness, _messages
from retrieval import format_docs

ROOT = Path(__file__).resolve().parent.parent


def latest(path):
    return {r["question"]: r for r in map(json.loads, path.read_text().splitlines())}


def controls():
    cases = []
    for name, stage, question, texts, answer, expected in GATE_CASES:
        documents = [{"id": None, "text": text, "metadata": {"source": f"synthetic-{i}.txt"}} for i, text in enumerate(texts)]
        cases.append({"id": name, "stage": stage, "expected": expected,
                      "state": {"question": question, "documents": documents, "generation": answer or v2.REFUSAL,
                                "citations": [{"id": i} for i in range(1, len(documents) + 1)]}})
    replay_inputs = json.loads((ROOT / "evals/results/replay_v2/2b50de398c1691e9b31b35d0e076907cffcbbe9ab664cf2a71be68a6b8b457c3/inputs.json").read_text())
    baseline = list(latest(ROOT / replay_inputs["baseline"]).values())
    for index, name in ((3, "incomplete-definition"), (7, "unsupported-retention-cause"), (9, "private-retry-scope")):
        row = baseline[index]
        cases.append({"id": name, "stage": "support", "expected": False,
                      "state": {"question": row["question"], "documents": row["documents"],
                                "generation": row["answer"], "citations": row["citations"]}})
    for index, (stage, expected, data) in enumerate(JUDGE_CASES):
        cases.append({"id": f"judge-{index}", "stage": stage, "expected": expected,
                      "data": {"question": "What does the context establish?", **data}})
    dev = latest(ROOT / "evals/results/verified/graph_v1/e13b5e6dd44ede10c5f55f8e798477049e4d60775d5eb064aa94836aa8be31e4/20261014T033524238124Z-1faf06c2/partial.jsonl")
    row = next(r for r in dev.values() if 'google-genai-hello-world' in r.get('answer', '') and 'task_queue' in r['question'])
    cases.append({"id": "exact-identifier-correctness", "stage": "correct", "expected": True,
                  "data": {"question": row["question"], "reference": "google-genai-hello-world", "answer": row["answer"]}})
    nova = latest(ROOT / "evals/results/verified/graph_v1/180fba46b3a145e2b5f19ccced278f664e2c4a06b5b792f1605f8fd07c3d87be/20261014T042408031523Z-f93405a4/partial.jsonl")
    row = next(r for r in nova.values() if 'private Nova' in r['question'])
    cases.append({"id": "private-timeout-faithfulness", "stage": "grounded", "expected": False,
                  "data": {"question": row["question"], "answer": row["answer"],
                           "context": [row["documents"][c["id"] - 1] for c in row["citations"]]}})
    assert len(cases) == 21 and len({c["id"] for c in cases}) == 21
    return cases


def inputs(cases):
    return {"scope": "Native development calibration; synthetic and previously reviewed real failures, not blind end-to-end accuracy.",
            "cases": cases, "model": llm.JUDGE_MODEL, "max_retries": llm.MAX_RETRIES,
            "requests_per_second": llm.REQUESTS_PER_SECOND, "temperature": 0,
            "code_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                            for p in ("graph_v2.py", "llm.py", "evals/calibrate_v21.py", "uv.lock")},
            "formatter_sha256": hashlib.sha256(inspect.getsource(format_docs).encode()).hexdigest()}


def main():
    cases = controls()
    metadata = inputs(cases)
    fingerprint = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    directory = ROOT / "evals/results/calibration_v21" / fingerprint
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "inputs.json", metadata)
    records = []
    for case in cases:
        path = directory / (case["id"] + ".json")
        record = json.loads(path.read_text()) if path.exists() else {"id": case["id"]}
        if "verdict" not in record:
            started = time.perf_counter()
            with get_usage_metadata_callback() as usage:
                try:
                    stage = case["stage"]
                    if stage in ("sufficiency", "support"):
                        state = {**case["state"], "documents": [Document(id=d.get("id"), page_content=d["text"], metadata=d["metadata"]) for d in case["state"]["documents"]]}
                        verdict = (v2.sufficient if stage == "sufficiency" else v2.supported)(state)[stage]
                        actual = verdict["passed"]
                    else:
                        schema = Correctness if stage == "correct" else Faithfulness
                        instruction = ("Decide whether the answer addresses the question and matches the reference in substance." if stage == "correct"
                                       else "Decide whether every factual claim in the answer is supported by the context for the exact entity and scope in the question. Public examples do not establish private configurations.")
                        verdict = llm.structured(schema, model=llm.JUDGE_MODEL).invoke(_messages(instruction, case["data"])).model_dump()
                        actual = verdict[stage]
                    record.update(verdict=verdict, expected=case["expected"], actual=actual, passed=actual is case["expected"])
                    record.pop("error", None)
                except Exception as exc:
                    record.update(error=type(exc).__name__, passed=False,
                                  retry_after=getattr(getattr(exc, "response", None), "headers", {}).get("retry-after"))
            old = record.get("usage", {})
            record["usage"] = {model: add_usage(old.get(model), usage.usage_metadata.get(model)) for model in sorted(old.keys() | usage.usage_metadata.keys())}
            record["seconds"] = record.get("seconds", 0) + time.perf_counter() - started
            write_json(path, record)
        records.append(record)
        print(case["id"], "error=" + record["error"] if "error" in record else "passed=" + str(record["passed"]), flush=True)
    assert inputs(cases) == metadata, "Calibration inputs changed during execution"
    result = {"artifact_dir": str(directory), "model": llm.JUDGE_MODEL, "n": len(cases),
              "scored": sum("verdict" in r for r in records), "passed": sum(r["passed"] for r in records),
              "missing": sum("verdict" not in r for r in records), "records": records}
    write_json(directory / "result.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
    if result["passed"] != result["n"]:
        raise SystemExit("Calibration has failed or missing controls; do not promote the model")


if __name__ == "__main__":
    main()
