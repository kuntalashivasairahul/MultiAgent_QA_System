"""Score any graph version against the golden set.

Run: uv run python evals/run_eval.py graph_v1 [limit]

Retrieval and generation are scored separately, so a regression tells you
which half broke rather than just that something did.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field

from llm import JUDGE_MODEL, structured

ROOT = Path(__file__).parent
GOLDEN = ROOT / "golden.jsonl"
RESULTS = ROOT / "results"


class Correctness(BaseModel):
    correct: bool = Field(description="Does the answer match the reference in substance?")


class Faithfulness(BaseModel):
    grounded: bool = Field(description="Is every claim supported by the context?")


def is_refusal(text: str) -> bool:
    """Deterministic — no judge call needed, and no judge variance either."""
    return "i don't know" in text.lower() or "i dont know" in text.lower()


def load_golden(limit: int | None = None) -> list[dict]:
    if not GOLDEN.exists():
        sys.exit(f"missing {GOLDEN} — run draft_golden.py and verify it first")
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    return rows[:limit] if limit else rows


def _load_partial(path: Path) -> dict[str, dict]:
    """Per-question outcomes already scored, keyed by question text.

    A full run takes tens of minutes under an 8,000 TPM ceiling. Losing all of
    it to one 429 at question 38 is not acceptable, so each question is appended
    as it completes and a rerun resumes from where it stopped.
    """
    if not path.exists():
        return {}
    return {
        r["question"]: r
        for r in (json.loads(l) for l in path.read_text().splitlines() if l.strip())
    }


def run_eval(graph_module: str, limit: int | None = None) -> dict:
    graph = importlib.import_module(graph_module).graph
    # Judges run on their own model, drawing from a separate TPM bucket, at low
    # reasoning effort because these are binary calls against a supplied reference.
    judge_correct = structured(Correctness, model=JUDGE_MODEL, reasoning_effort="low")
    judge_grounded = structured(Faithfulness, model=JUDGE_MODEL, reasoning_effort="low")
    rows = load_golden(limit)

    RESULTS.mkdir(exist_ok=True)
    partial_path = RESULTS / f"{graph_module}.partial.jsonl"
    done = _load_partial(partial_path)
    if done:
        print(f"  resuming: {len(done)} already scored", flush=True)

    for i, row in enumerate(rows, 1):
        if row["question"] in done:
            continue
        out = graph.invoke({"question": row["question"]})
        answer = out.get("generation", "")
        docs = out.get("documents", [])
        print(f"  [{i}/{len(rows)}] {row['bucket']:<13} {row['question'][:58]}", flush=True)

        rec = {"question": row["question"], "bucket": row["bucket"]}
        if row["bucket"] == "unanswerable":
            # The only correct behaviour here is declining.
            rec["refused"] = is_refusal(answer)
            rec["correct"] = rec["refused"]
        else:
            verdict = judge_correct.invoke(
                f"Reference answer:\n{row['answer']}\n\nGiven answer:\n{answer}\n\n"
                "Does the given answer match the reference in substance?"
            )
            rec["correct"] = bool(verdict.correct)
            if docs:
                context = "\n\n".join(d.page_content for d in docs)
                fverdict = judge_grounded.invoke(
                    f"Context:\n{context[:6000]}\n\nAnswer:\n{answer}\n\n"
                    "Is every claim in the answer supported by the context?"
                )
                rec["grounded"] = bool(fverdict.grounded)
                expected = set((row.get("source") or "").split(","))
                got = {d.metadata.get("source") for d in docs}
                rec["recalled"] = bool(expected & got)

        done[row["question"]] = rec
        with partial_path.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")

    scored = [done[r["question"]] for r in rows if r["question"] in done]

    def mean(key: str, subset: list[dict] | None = None) -> float | None:
        xs = [r[key] for r in (scored if subset is None else subset) if key in r]
        return round(sum(xs) / len(xs), 3) if xs else None

    result = {
        "graph": graph_module,
        "n": len(scored),
        "correctness": mean("correct"),
        "faithfulness": mean("grounded"),
        "recall_at_k": mean("recalled"),
        "refusal_rate": mean("refused", [r for r in scored if r["bucket"] == "unanswerable"]),
    }
    (RESULTS / f"{graph_module}.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    module = sys.argv[1] if len(sys.argv) > 1 else "graph_v1"
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(run_eval(module, cap), indent=2))
