# Verified evaluation results

Frozen repaired baseline at `9dcd9ef`. These values describe that code/index snapshot, not the current v2 worktree. The original table and raw artifacts below are preserved.

Dataset: golden.jsonl. These full evaluations matched inputs at the frozen baseline; metric coverage is visible below.

| Version | n | Correct | Answerable correct | Faithful | Source recall@k | All sources@k | Exact refusal | Status |
|---|---|---|---|---|---|---|---|---|
| graph_v0 | 40 | 0.475 | 0.406 | — | — | — | 0.750 | complete |
| graph_v1 | 40 | 0.675 | 0.594 | 0.938 | 0.781 | 0.719 | 1.000 | complete |

## graph_v0

Run: [20261014T033131416222Z-0b49247b](results/verified/graph_v0/4915c5f3722616cbde1f5010449a96ab9cf460ee6ad054aa0bb83b129c661e53/20261014T033131416222Z-0b49247b/result.json). Fingerprint: 4915c5f3722616cbde1f5010449a96ab9cf460ee6ad054aa0bb83b129c661e53. Retrieval k: None.

| Metric | Eligible | Scored | Missing |
|---|---:|---:|---:|
| correctness | 40 | 40 | 0 |
| answerable_correctness | 32 | 32 | 0 |
| faithfulness | 0 | 0 | 0 |
| recall_at_k | 0 | 0 | 0 |
| all_sources_rate | 0 | 0 | 0 |
| any_source_rate | 0 | 0 | 0 |
| refusal_rate | 8 | 8 | 0 |

## graph_v1

Run: [20261014T033524238124Z-1faf06c2](results/verified/graph_v1/e13b5e6dd44ede10c5f55f8e798477049e4d60775d5eb064aa94836aa8be31e4/20261014T033524238124Z-1faf06c2/result.json). Fingerprint: e13b5e6dd44ede10c5f55f8e798477049e4d60775d5eb064aa94836aa8be31e4. Retrieval k: 5.

| Metric | Eligible | Scored | Missing |
|---|---:|---:|---:|
| correctness | 40 | 40 | 0 |
| answerable_correctness | 32 | 32 | 0 |
| faithfulness | 32 | 32 | 0 |
| recall_at_k | 32 | 32 | 0 |
| all_sources_rate | 32 | 32 | 0 |
| any_source_rate | 32 | 32 | 0 |
| refusal_rate | 8 | 8 | 0 |

Source recall counts evidence groups, accepting reviewed alternative paths. All-sources success requires every group. Exact refusal is a contract check, not a direct hallucination measure. Model-only performance cannot establish training-data provenance. Development and holdout scores must be interpreted separately; small samples have substantial uncertainty.

## Review caveat

Correctness above is an automated judge label. [A retained-output review](JUDGE_REVIEW.md) confirms one false-negative on dev-08; the raw verdict and table are preserved. Correcting that case alone would give 28/40, but the remaining labels are not independently certified. Passing eight calibration controls does not prove every judge verdict is correct.
