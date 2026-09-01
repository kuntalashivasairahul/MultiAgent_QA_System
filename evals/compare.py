"""Build the comparison table across every graph version that has results.

Run: uv run python evals/compare.py          (reuses cached results)
     uv run python evals/compare.py --run    (re-runs every version)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_eval import RESULTS, run_eval  # noqa: E402

ROOT = Path(__file__).parent
VERSIONS = [p.stem for p in sorted(Path(__file__).parent.parent.glob("graph_v*.py"))]
COLS = [("correctness", "Correct"), ("faithfulness", "Faithful"),
        ("recall_at_k", "Recall@5"), ("refusal_rate", "Refuses")]


def cell(v) -> str:
    return "—" if v is None else f"{v:.3f}"


def main() -> None:
    rerun = "--run" in sys.argv
    rows = []
    for v in VERSIONS:
        cached = RESULTS / f"{v}.json"
        if rerun or not cached.exists():
            print(f"running {v}")
            rows.append(run_eval(v))
        else:
            rows.append(json.loads(cached.read_text()))

    head = "| Version | n | " + " | ".join(c[1] for c in COLS) + " |"
    sep = "|---" * (len(COLS) + 2) + "|"
    body = [
        f"| {r['graph']} | {r['n']} | " + " | ".join(cell(r[c[0]]) for c in COLS) + " |"
        for r in rows
    ]
    table = "\n".join([head, sep, *body])
    print("\n" + table)

    (ROOT / "RESULTS.md").write_text(
        "# Evaluation Results\n\n"
        "Identical golden set across every version. Retrieval and generation\n"
        "scored separately. `Refuses` is measured only on the unanswerable bucket.\n\n"
        f"{table}\n\n"
        "**Reading v0:** it retrieves nothing. High correctness there means the\n"
        "model already knows this corpus, and the retrieval numbers below it are\n"
        "not measuring what they appear to.\n"
    )
    print(f"\nwrote {ROOT / 'RESULTS.md'}")


if __name__ == "__main__":
    main()
