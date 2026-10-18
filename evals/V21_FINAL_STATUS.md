# V2.1 final verification status

Selected stable implementation: **`b024062`**. Accepted engineering assessment: **8.63/10** using the fixed rubric. On 18 October 2026 the owner stopped the 9/10 improvement goal and requested a résumé audit, a plan for missing claims, testing/documentation and a stable GitHub push. This is a coding-assistant assessment of a public-document research prototype, not independent certification or a promise of 90% answer accuracy. No 9/10 claim is made.

## Verified repairs

- **110 full-suite tests passed in 12.51s in the fresh stable-release audit**, including four real corpus/index integration tests.
- A frozen `b024062` checkout without corpus, index, `.env` or API credentials passed **106 offline tests in 7.86s**, with four integration tests explicitly deselected. It reused the installed locked environment; this was not a fresh dependency installation. `uv sync --frozen` verified the locked environment earlier this session.
- Current frozen-code hybrid retrieval recovered **11/11 selected facts, 7/7 complete diagnostic contexts and 33/33 required source groups** on the corrected development references. These are development-tuned source diagnostics, not independent answer accuracy. See the [retained diagnostic](results/section_retrieval/148bcae8cb7adc92f512094583b7046ad96604e01b3cfbe87d8ab64e4eb97874/result.json).
- Durable synchronous graph-node recovery, competing-writer protection, cumulative persisted graph/judge usage, safe retry metadata, and checkpoint ownership during repairing reads have passing regressions.
- The 14,414-record index was rebuilt and matched canonical text/metadata, preserved the previous snapshot and passed idempotence checks. The digest does not cover embedding coordinates or adversarial local filesystem changes.
- Evidence JSON now preserves Unicode. A controlled native replay fixed the observed em-dash/control-character quote corruption; the ordinary native development run also completed that question. [Probe](results/unicode_prompt_probe_v21.json).
- Prose quotes can now recover whitespace beside fenced code while preserving literal code and returning exact contiguous source spans. The actual external-storage failure and all three rejected verdicts are [preserved](results/mixed_prose_quote_diagnosis_v21.json) and replay successfully under the fix. Tests reject changed facts/code, spans bridging code, unclosed/short-closing fences and nested-fence normalization.
- Evidence validation still allows at most three attempts, retains rejected verdicts, and never retries a valid semantic negative. The preceding UTF8 checker/profile passed [21/21 native calibration controls](results/calibration_v21/cb55709fe327a2634541d758b44f38d040e27ffbe349cfbd9d11241a2c2edbc9/result.json); that is pre-mixed-prose-fix component evidence, not a new native run of `b024062`.
- Current evaluation defaults to the [versioned reference correction](REFERENCE_ERRATA_V21.md). Content-addressed comparison reports preserve historical baseline/holdout reports; regression tests cover both behaviors.

The [validation snapshot](results/validation_mixed_v21.json) retains outcomes, scope limits and prepared native input identities.

## Retained native evidence and stopped evaluation

The preceding `e9a1185` run is **incomplete: 21/40 fully scored, 19 missing**. It stopped after three rejected external-storage prose quotes and native daily-token rate limits. Its [aggregate and coverage](results/verified/graph_v2_1/93db52feb91110638d5cdaeb0c86490d725500fbcc5ab4e35c4038b6f6c64828/20261018T065045922242Z-a6077f8b/result.json), [raw answers/audits](results/verified/graph_v2_1/93db52feb91110638d5cdaeb0c86490d725500fbcc5ab4e35c4038b6f6c64828/20261018T065045922242Z-a6077f8b/partial.jsonl), and [worker log](results/native_before_mixed_prose_fix_v21.log) remain preserved. These are not final-current-version metrics and missing rows are not correct answers or refusals.

The [partial source review](results/review_utf8_v21_partial.json) covers all 21 scored outputs, checks 251 retrieved documents against canonical text/metadata and 79 literal gate quotes, and preserves automated labels. Dev-16 is a genuine false refusal: retrieval supplied the Local Activity definition, but the generator added unsupported “high-throughput”; support correctly rejected it. Dev-00 has possible signup-requirement overstatement; dev-15 adds an implicit workflow-state/query interpretation to the exact store names. Both qualifications remain visible alongside passing automated labels. SDK/CLI examples were reviewed as text, not executed.

The old confirmation sets `confirmation_final_v21`, `confirmation_repaired_v21` and `confirmation_utf8_v21` were each withdrawn **before native execution** because implementation changed. [Twelve newly authored questions](confirmation_prose_v21.jsonl) now follow freeze `b024062`; [provenance](confirmation_prose_v21_provenance.json) records literal source checks, authorship timing, dataset identity, index identity and the explicit native profile. No retrieval/model outcomes selected these questions. Shared authorship and overlapping Temporal/SDK topics limit their independence.

The final `b024062` development/confirmation run **did not start**. The owner stopped the improvement run before the scheduled 07:30 UTC launch. The queued supervisor (PID 13293, tool session 91670) received SIGINT and exited **130**; process inspection confirmed no remaining native evaluator/supervisor. No new provider call was made in the résumé/release audit. The fresh confirmation set remains unexecuted.

The old quota/recovery evidence and manual resumer are retained for reproducibility. A two-hour refill heuristic applies if daily quota interrupts quote validation; it is not guaranteed provider capacity. Failed calls within an unfinished node may repeat after an outage. Local SQLite recovery files are Git-ignored; portable JSONL alone cannot recover a pending graph node on a different machine.

The [résumé claim audit](../docs/RESUME_AUDIT.md) records what is implemented and missing. The [v3 plan](../docs/V3_RESUME_ALIGNMENT_PLAN.md) covers a bounded quality-driven retrieval retry and FastAPI interface; these features are not part of stable v2.1. Release checks and publication evidence are recorded in [stable release verification](results/stable_v21_release_verification.json).

Manual recovery is available only if the owner later chooses to resume evaluation:

```sh
LANGSMITH_TRACING=false GROQ_MODEL=openai/gpt-oss-120b GROQ_JUDGE_MODEL=qwen/qwen3.8-27b GROQ_MAX_RETRIES=8 GROQ_RPS=0.25 uv run python -u evals/results/final_native_resume.txt
```

Individual equivalent commands:

```sh
LANGSMITH_TRACING=false GROQ_MODEL=openai/gpt-oss-120b GROQ_JUDGE_MODEL=qwen/qwen3.8-27b GROQ_MAX_RETRIES=8 GROQ_RPS=0.25 uv run python evals/run_eval.py graph_v2_1 --dataset evals/golden_current_v21.jsonl
LANGSMITH_TRACING=false GROQ_MODEL=openai/gpt-oss-120b GROQ_JUDGE_MODEL=qwen/qwen3.8-27b GROQ_MAX_RETRIES=8 GROQ_RPS=0.25 uv run python evals/run_eval.py graph_v2_1 --dataset evals/confirmation_prose_v21.jsonl
```

Do not use `--fresh` for quota recovery. Changing fingerprinted implementation, model, references or lock creates a new attempt. Keep the freeze intact while collecting final evidence. Existing `.env` preferences remain preserved; the commands select the measured profile explicitly. No billing change or production deployment is included in this checkpoint. GitHub publication is documented separately in the release verification.

## Deferred requirements for any future 9/10 claim

The owner has stopped this work. If the target is resumed, complete all eligible metrics on final development 40 and fresh confirmation 12 with zero missing values. Source-review confirmation and development failures/suspected grader errors, preserving automated labels alongside adjudication. Report graph/judge usage, operational failures, uncertainty, false refusals, unsupported answers and reference changes. Apply the fixed rubric; resolve major findings before promoting the score. An incomplete run cannot earn nine.

[GitHub CI run 39108281218](https://github.com/kuntalashivasairahul/MultiAgent_QA_System/actions/runs/39108281218) passed on published stable code commit `219af43`: fresh locked Linux setup, 106 offline tests, a fresh 14,414-document index and four integration tests. A documentation-only follow-up records this result without another identical index build. Windows, independent human/field validation, private-data isolation and production deployment remain unverified or outside scope. Semantic gates remain fallible despite literal quotes.
