"""Compare full evaluations on current inputs; preserve the historical baseline table."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.run_eval import GOLDEN, run_eval

ROOT = Path(__file__).resolve().parent
VERSIONS = [p.stem for p in sorted(ROOT.parent.glob("graph_v*.py"))]
COLS = [
    ("correctness", "Correct"), ("answerable_correctness", "Answerable correct"),
    ("faithfulness", "Faithful"), ("recall_at_k", "Source recall@k"),
    ("all_sources_rate", "All sources@k"), ("refusal_rate", "Exact refusal"),
]


def cell(v) -> str:
    return "—" if v is None else str(v) if isinstance(v, int) else f"{v:.3f}"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Fresh inference, preserving prior attempts")
    parser.add_argument("--dataset", type=Path, default=GOLDEN)
    args = parser.parse_args(argv)
    rows = [run_eval(v, dataset=args.dataset, fresh=args.run) for v in VERSIONS]
    head = "| Version | n | " + " | ".join(c[1] for c in COLS) + " | Status |"
    sep = "|---" * (len(COLS) + 3) + "|"
    body = [
        f"| {r['graph']} | {r['n']} | " + " | ".join(cell(r[c[0]]) for c in COLS) + f" | {r['status']} |"
        for r in rows
    ]
    details = []
    for r in rows:
        artifact = Path(r["artifact_dir"])
        relative = Path(os.path.relpath(artifact, ROOT)).as_posix()
        details.append(f"\n## {r['graph']}\n\nRun: [{r['run_id']}]({relative}/result.json). "
                       f"Fingerprint: {r['fingerprint']}. Retrieval k: {r['retrieval_k']}.\n\n"
                       "| Metric | Eligible | Scored | Missing |\n|---|---:|---:|---:|\n" +
                       "\n".join(f"| {m} | {c['eligible']} | {c['scored']} | {c['missing']} |"
                                 for m, c in r["coverage"].items()))
    path = ROOT / ("RESULTS_VERIFIED.md" if args.dataset.resolve() == GOLDEN.resolve() else "RESULTS_HOLDOUT.md")
    path.write_text(
        "# Verified evaluation results\n\nDataset: " + args.dataset.name + ". "
        "Only current-input full evaluations appear here; missing metrics are visible below.\n\n" +
        "\n".join([head, sep, *body]) + "\n" + "\n".join(details) +
        "\n\nSource recall counts evidence groups, accepting reviewed alternative paths. "
        "All-sources success requires every group. Exact refusal is a contract check, not a direct hallucination measure. "
        "Model-only performance cannot establish training-data provenance. "
        "Development and holdout scores must be interpreted separately; small samples have substantial uncertainty.\n",
        encoding="utf-8",
    )
    print(path.read_text())
    if any(r["status"] != "complete" for r in rows):
        raise SystemExit("Incomplete evaluation; not a phase-gate pass")


if __name__ == "__main__":
    main()
