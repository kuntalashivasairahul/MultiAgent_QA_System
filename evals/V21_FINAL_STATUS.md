# V2.1 final verification status

Selected implementation: **`9d39840`**. Overall project-quality target: **9/10**; current evidence-based score: **8.63/10**. This is a coding-assistant engineering assessment of a public-document research prototype, not independently certified answer accuracy. The goal is not complete.

## Completed

- 96 full-suite tests pass, including real retrieval/integrity integration.
- A committed clean snapshot without API credentials, corpus, index or `.env` passes 92 offline tests; four integration tests are explicitly deselected there and passed in the full suite.
- 11/11 frozen diagnostic facts, 7/7 complete diagnostic contexts, 32/32 required source groups; dense-twelve and legacy-section-ten controls retained.
- Durable synchronous graph-node recovery, competing-writer protection, cumulative persisted graph/judge usage and safe retry metadata; real SQLite recovery tests pass.
- Same-ID corruption is rejected. Real 14,414-document content equals the previous snapshot; rebuild is idempotent and old collections remain recoverable.
- Bounded correction of invalid literal-quote verdicts, preserving rejected evidence/audits; strict validation is retained.
- 21/21 native controls on the final grading profile, and a versioned source correction for the old pricing reference error.
- Twelve new confirmation questions source-reviewed after the final implementation freeze. Earlier confirmation questions remain preserved but were withdrawn before inference.

## Waiting on provider quota

At this checkpoint the final development run has **4/40 fully scored rows**, **36 missing native outputs**, and no completed confirmation run. Both models returned native daily-token errors: limit **200,000 tokens/day**. Reported retry delays reached roughly 12–23 minutes for an individual pending request; that does not guarantee enough capacity for all remaining work. Full completion can require substantially longer. Missing outputs are operational failures, not correct answers or refusals.

Current development attempt: [inputs](results/verified/graph_v2_1/22c35431fd2520d320ff1b5ace2018fd2e5672119db5a8d31084e4c9b68e394f/20261014T152435540331Z-c2ddd6c6/inputs.json), [partial results](results/verified/graph_v2_1/22c35431fd2520d320ff1b5ace2018fd2e5672119db5a8d31084e4c9b68e394f/20261014T152435540331Z-c2ddd6c6/partial.jsonl), [aggregate with denominators](results/verified/graph_v2_1/22c35431fd2520d320ff1b5ace2018fd2e5672119db5a8d31084e4c9b68e394f/20261014T152435540331Z-c2ddd6c6/result.json). The aggregate may advance as the local resumer runs; inspect its actual `status` and coverage before interpreting it.

The [local resumer](results/final_native_resume.txt) is running with tracing disabled and the frozen profile. It waits for attempt ownership, resumes only matching inputs, retains valid verdicts, respects reported numeric cooldowns, and runs the replacement confirmation after development completes. Its assertions enforce the same fingerprint/attempt across resumptions. It needs this machine/process and network to remain available. Local graph SQLite files are Git-ignored; moving only the portable JSONL cannot recover a pending graph node on another machine. No billing change or deployment was made.

To resume if the process stops, from the project root:

```sh
LANGSMITH_TRACING=false GROQ_JUDGE_MODEL=qwen/qwen3.8-27b GROQ_MAX_RETRIES=8 uv run python -u evals/results/final_native_resume.txt
```

Individual equivalent commands, preserving input identity:

```sh
LANGSMITH_TRACING=false GROQ_JUDGE_MODEL=qwen/qwen3.8-27b GROQ_MAX_RETRIES=8 uv run python evals/run_eval.py graph_v2_1 --dataset evals/golden_current_v21.jsonl
LANGSMITH_TRACING=false GROQ_JUDGE_MODEL=qwen/qwen3.8-27b GROQ_MAX_RETRIES=8 uv run python evals/run_eval.py graph_v2_1 --dataset evals/confirmation_repaired_v21.jsonl
```

Do not use `--fresh` for quota recovery. Changing any fingerprinted code, model setting or reference selects a different attempt; keep the freeze intact while collecting final evidence. Existing `.env` preferences are preserved; explicit flags above select the measured grader/retry profile.

## Required before claiming 9/10

Finish all eligible metrics on both datasets with zero missing values. Source-review all confirmation answers and development failures/suspected grader errors, preserving automated labels alongside adjudication. Report reported graph/judge usage and operational failures, uncertainty, false refusals, unsupported answers and reference changes. Apply the fixed scorecard weights again; repair remaining major findings and use newly authored confirmation if the selected implementation changes. Do not promote partial metrics or round the current 8.63 to nine.

Windows execution, hosted GitHub CI, independent human/field validation, private-data isolation and production deployment remain unverified or outside scope. SDK examples were source-reviewed, not executed against every SDK runtime. Model-based gates can still misjudge semantic support even with valid literal quotes.
