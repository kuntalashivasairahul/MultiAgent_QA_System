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

from llm import get_llm

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


def run_eval(graph_module: str, limit: int | None = None) -> dict:
    graph = importlib.import_module(graph_module).graph
    judge = get_llm()
    rows = load_golden(limit)

    correct, grounded, recalled = [], [], []
    refusals_on_unanswerable = []

    for i, row in enumerate(rows, 1):
        out = graph.invoke({"question": row["question"]})
        answer = out.get("generation", "")
        docs = out.get("documents", [])
        print(f"  [{i}/{len(rows)}] {row['bucket']:<13} {row['question'][:58]}", flush=True)

        if row["bucket"] == "unanswerable":
            # The only correct behaviour here is declining.
            refusals_on_unanswerable.append(is_refusal(answer))
            correct.append(is_refusal(answer))
            continue

        verdict = judge.with_structured_output(Correctness).invoke(
            f"Reference answer:\n{row['answer']}\n\nGiven answer:\n{answer}\n\n"
            "Does the given answer match the reference in substance?"
        )
        correct.append(bool(verdict.correct))

        if docs:
            context = "\n\n".join(d.page_content for d in docs)
            fverdict = judge.with_structured_output(Faithfulness).invoke(
                f"Context:\n{context[:6000]}\n\nAnswer:\n{answer}\n\n"
                "Is every claim in the answer supported by the context?"
            )
            grounded.append(bool(fverdict.grounded))
            expected = set((row.get("source") or "").split(","))
            got = {d.metadata.get("source") for d in docs}
            recalled.append(bool(expected & got))

    def mean(xs: list[bool]) -> float | None:
        return round(sum(xs) / len(xs), 3) if xs else None

    result = {
        "graph": graph_module,
        "n": len(rows),
        "correctness": mean(correct),
        "faithfulness": mean(grounded),
        "recall_at_k": mean(recalled),
        "refusal_rate": mean(refusals_on_unanswerable),
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{graph_module}.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    module = sys.argv[1] if len(sys.argv) > 1 else "graph_v1"
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(run_eval(module, cap), indent=2))
