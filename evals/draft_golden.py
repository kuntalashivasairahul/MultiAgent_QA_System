"""Draft golden-set candidates from the corpus. Output MUST be human-verified.

Run: uv run python evals/draft_golden.py
Writes evals/golden.draft.jsonl. Check every answer against the corpus, then
rename to evals/golden.jsonl. An unverified golden set measures nothing.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field

from ingest import load_chunks
from llm import structured

OUT = Path(__file__).parent / "golden.draft.jsonl"
TARGET = {"direct": 12, "jargon": 8, "multihop": 8, "ambiguous": 4}

# Authored by hand, never sampled: these must be plausible questions whose
# answers are genuinely absent from the docs. This bucket is what separates
# a system that refuses from one that fabricates.
UNANSWERABLE = [
    "How much does Temporal Cloud cost per million actions?",
    "What is the home address of Temporal's CEO?",
    "How many employees does Temporal Technologies have?",
    "What was Temporal's revenue last quarter?",
    "Which venture capital firm led Temporal's Series C?",
    "What is the WiFi password at Temporal's head office?",
    "What is our company's internal on-call escalation policy for Temporal?",
    "How many Temporal workflows did Netflix run yesterday?",
]


class QA(BaseModel):
    question: str = Field(description="A question answerable only from the passage")
    answer: str = Field(description="A concise answer, drawn only from the passage")


def _draft(llm, instruction: str, passage: str) -> QA | None:
    try:
        return llm.invoke(
            f"{instruction}\n\nPassage:\n{passage[:2500]}"
        )
    except Exception as exc:  # noqa: BLE001 - drafting is best-effort
        print(f"  skipped: {exc}", file=sys.stderr)
        return None


INSTRUCTIONS = {
    "direct": "Write one factual question answered directly by this passage, and its answer.",
    "jargon": (
        "Write one question about the Temporal-specific technical term in this "
        "passage, using the exact term. Then answer it."
    ),
    "ambiguous": (
        "Write one vaguely-worded question a confused user might ask that this "
        "passage answers. Do not use the passage's exact wording. Then answer it."
    ),
    "multihop": (
        "These two passages are from different documents. Write one question "
        "that requires BOTH to answer, then answer it."
    ),
}


def main() -> None:
    random.seed(0)
    chunks = [c for c in load_chunks() if len(c.page_content) > 400]
    glossary = [c for c in chunks if "glossary" in c.metadata["source"]]
    llm = structured(QA, temperature=0.3)
    rows = []

    for bucket, n in TARGET.items():
        pool = glossary if (bucket == "jargon" and glossary) else chunks
        print(f"{bucket}: drafting {n}")
        for _ in range(n):
            if bucket == "multihop":
                a, b = random.sample(chunks, 2)
                passage = f"[A: {a.metadata['source']}]\n{a.page_content}\n\n[B: {b.metadata['source']}]\n{b.page_content}"
                source = f"{a.metadata['source']},{b.metadata['source']}"
            else:
                c = random.choice(pool)
                passage, source = c.page_content, c.metadata["source"]
            qa = _draft(llm, INSTRUCTIONS[bucket], passage)
            if qa:
                rows.append(
                    {"question": qa.question, "answer": qa.answer,
                     "bucket": bucket, "source": source}
                )

    for q in UNANSWERABLE:
        rows.append({"question": q, "answer": "I don't know.",
                     "bucket": "unanswerable", "source": None})

    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"\nwrote {len(rows)} drafts -> {OUT}")
    print("VERIFY EVERY ANSWER, then rename to evals/golden.jsonl")


if __name__ == "__main__":
    main()
