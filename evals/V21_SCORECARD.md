# V2.1 audit and improvement scorecard

Target requested: finish the version, test/review it, fix findings, and repeat until the overall project score reaches 9/10. The score retains the original audit's research-prototype scope and weights. It is an engineering assessment by the coding assistant, not an independently certified rating or a claim of 90% future answer accuracy. Measured answer quality is reported separately.

## Fixed rubric

| Area | Weight | Evidence needed for 9 or above |
|---|---:|---|
| Architecture and scope | 20% | Clear shared graph/citation contract; bounded retrieval and execution; reliable reuse; no unresolved major correctness/security finding in the supported public-corpus scope |
| Ingestion and retrieval | 15% | Canonical code/content and rebuild integrity; at least 10/11 frozen diagnostic facts and 6/7 complete diagnostic contexts; at least 90% all-required-source coverage on development; enforced context limits and audited remaining misses |
| Evaluation validity | 25% | Immutable input identities and paid-work retention; complete eligible metrics on the final 40-question development run and a newly authored, source-reviewed confirmation of at least 12 questions; explicit judge adjudication, uncertainty, cost and abstention limits; no silent relabeling or partial-score promotion |
| Testing | 15% | Behavioral and trust-boundary tests for changes; real retrieval/index checks; outage/resume/cache/data-integrity regressions; reproducible automated checks with no unexplained failures |
| Reproducibility and runtime reliability | 15% | Pinned setup/index; durable graph-node resumption; accurate accumulated reported usage; bounded execution and recoverable provider errors; competing run protection; tested safe rebuild and documented recovery |
| Documentation | 10% | Usable setup/evaluation commands; current evidence links; versioned results; explicit data flows, supported scope, remaining risks and provenance; no claimed production/private-data/independent validation without proof |

The score is the weighted mean of the six area ratings. Missing fresh evaluation, unresolved major findings, or hidden metric gaps cap the overall rating below 9 regardless of test count or documentation. Stronger claims about general accuracy, private-data service readiness, or independent review require separate evidence. Retrieval thresholds use frozen development labels and are not a representative accuracy estimate. Confirmation questions must be authored after freezing the selected implementation and must not be used to tune it.

## Iteration 0: audited d4c8b63

| Area | Score | Reason |
|---|---:|---|
| Architecture and scope | 8.0 | Shared gates and citation contract are clear; retrieval selection and evaluation failure lifecycle remain weak |
| Ingestion and retrieval | 6.0 | Data preservation and bounded expansion work, but only 5/11 selected facts, 1/7 complete diagnostic contexts and 23/32 complete source groups |
| Evaluation validity | 7.5 | Strong fingerprints/evidence retention, but current fresh confirmation is incomplete and known grader false-positives remain material |
| Testing | 8.5 | 82 tests pass; real command regression and cache isolation covered; durable node resumption, competing writers and broader retrieval cases are not covered |
| Reproducibility and runtime reliability | 7.0 | Pinned/idempotent index and matching-input answer resume; no durable successful-node resume, cumulative failed-attempt usage, or exclusive attempt ownership |
| Documentation | 9.0 | Actual scope, limited evidence, quota failures and next work are clearly disclosed |
| **Weighted overall** | **7.60** | **Not 9/10; no broad current-version quality result exists** |

Verification: `LANGSMITH_TRACING=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q` -> **82 passed in 9.71s**. Retrieval evidence is the preserved [40-question diagnostic](results/section_retrieval/f9d9edaecd10f25d344e01eae89a27f9acacb20ff7c619d02c62c32c91944ec4/result.json). Native confirmation remains incomplete as described in [v2.1 initial results](V21_STATUS.md).

## Findings to resolve

1. **Major — incomplete answer-bearing context.** Strict section expansion cannot discover missing SDK/source anchors; early sections consume the budget. More text has not solved six of seven diagnosed contexts.
2. **Major — successful graph nodes are not durable across evaluation retries.** A later support/grader failure discards paid successful sufficiency/generation work from the resumable answer checkpoint. Resume reruns those calls.
3. **Major — graph usage and timing overwrite earlier failed-attempt work.** `run_eval` assigns the latest callback/time instead of accumulating reported graph work across resumptions. Existing totals are final-attempt observations, not complete run cost.
4. **Major — incomplete native confirmation.** A complete paired/final current-input study, broader fresh questions and reviewed actual errors are still needed before a high quality assessment.
5. **Moderate — no exclusive attempt ownership.** Concurrent resumptions can append to the same checkpoint and duplicate paid calls. Existing atomic aggregate writing alone does not prevent this.
6. **Moderate — index rebuilding verifies IDs/count but not existing content.** Same-ID stored corruption could survive a resumed build. Reproduce and address the supported local integrity boundary before claiming verified snapshots.
7. **Moderate — automated checks require a prepared local index and lack an automated clean-environment workflow.** Separate offline behavioral checks from the explicit retrieval integration prerequisite, without silently skipping integration in release validation.

This file will retain iteration results and score changes with their supporting artifacts. Scores will not be increased merely because a fix was proposed or a test was added.

## Iteration 1: runtime and integrity repairs

Implemented durable synchronous SQLite node checkpoints for v2/v2.1 evaluation, per-attempt/fingerprint ownership, accumulated persisted-attempt graph usage/time, and safe retry metadata. Real SQLite tests reopen the checkpoint after a support outage and after an answer-write failure, verifying completed paid nodes are not repeated. A competing writer is rejected and ownership releases on close. Provider outages remain errors.

Reproduced same-ID content corruption surviving an index rebuild. Builds now compare existing and completed stored text/metadata with canonical chunks, publish a content digest, and verify that digest when opening a snapshot. Validation is cached for the immutable collection during a process; this is accidental-corruption detection, not protection against an attacker controlling local files. Embeddings are provenance-pinned, not covered by the text/metadata digest.

The rebuilt real index retains **14,414 chunks**. Current full suite: **87 passed in 7.81s**. Three actual-corpus/index tests are explicitly marked integration; they still run in the full suite. No integration check was silently dropped.

| Area | Updated score |
|---|---:|
| Architecture and scope | 8.5 |
| Ingestion and retrieval | 6.0 |
| Evaluation validity | 7.5 |
| Testing | 9.0 |
| Reproducibility and runtime reliability | 8.5 |
| Documentation | 9.0 |
| **Weighted overall** | **8.00** |

Findings 2, 3, 5 and 6 now have implemented fixes and passing regressions. Findings 1, 4 and clean-environment verification from 7 remain open. No 9/10 claim is made. Retrieval prototypes are development experiments, not shipped gains or native accuracy evidence.
