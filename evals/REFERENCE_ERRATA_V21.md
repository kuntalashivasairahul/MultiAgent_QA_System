# Development-reference erratum

The frozen `golden.jsonl` labels **dev-32, “How much does Temporal Cloud cost per million actions?”**, unanswerable with the reference `I don't know.`. The pinned public corpus actually contains an Actions pricing table and starting price in `evaluate/temporal-cloud/pricing.mdx`. The final v2.1 native answer cites those chunks. This is a reference-label error, not evidence of an unsupported answer. These are historical corpus facts, not a live pricing recommendation.

The original question, bucket and automated labels remain unchanged in the frozen native comparison. The final review reports the label error separately; it does not silently promote the raw score. [golden_current_v21.jsonl](golden_current_v21.jsonl) explicitly revises only this row to an answerable direct question, with source proof and an erratum marker. All 40 questions remain in their original order; the revised bucket counts are 13 direct, 8 jargon, 8 multihop, 4 ambiguous and 7 unanswerable. Native results for the frozen dataset are not presented as native evaluation against these revised references.

For future current-reference development runs, use:

```sh
LANGSMITH_TRACING=false GROQ_JUDGE_MODEL=qwen/qwen3.8-27b uv run python evals/run_eval.py graph_v2_1 --dataset evals/golden_current_v21.jsonl
```

Since implementation `e9a1185`, the unqualified evaluation and comparison CLI selects `golden_current_v21.jsonl`. To reproduce the historical references, explicitly pass `--dataset evals/golden.jsonl`. The corrected file is a versioned source audit, not a new confirmation set. Shared authorship and model-based judging still limit the strength of resulting accuracy claims. Comparison reports have content-addressed filenames and preserve the frozen development/holdout reports.
