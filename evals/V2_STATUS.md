# Evidence-gated v2: implementation and verification status

Baseline freeze: `9dcd9ef`. V2 implementation freeze: `cd815e7`, before authoring the [new four-question confirmation set](CONFIRMATION_V2.md). No retrieval/index/model changes are bundled into v2.

Implemented: exact-question evidence sufficiency, generation through unchanged v1, cited-claim support, canonical refusal on a negative semantic verdict, checked verbatim evidence quotes, retained rejected drafts, independent ablation identities, metric coverage, generation/gate token metadata and latency. Grader/provider/quote-validation errors remain operational errors.

Verified locally: **49 tests passed**. [Live synthetic calibration](v2_calibration.json): **8/8 passed**, balancing positive and negative controls, including partial multi-hop evidence, private scope, unsupported extra claims, and injections. These controls establish limited integration behavior, not corpus accuracy or injection immunity.

The first fresh v2 answer is fully judged successfully: serialization runs the Payload Converter before the Payload Codec, with both gates passing, their quotes validated, and correctness/faithfulness judges both passing. Provider usage was 1,846 generator tokens plus 4,183 gate tokens on this single question. Its observed 587-second graph time includes a 573-second quota wait and cannot estimate intrinsic gate latency. The remaining three questions and completed replay comparison are still pending; this is not an aggregate quality result.

## Live comparison remains incomplete

Both models reached provider quotas during the fresh comparison. Paid successful answers and completed replay checks are retained. External orchestration respects provider retry-after delays within the failed call, preserving completed graph nodes. It changes neither prompts nor models. Its source and quota observations are retained separately; quota waits affect observed latency and are not intrinsic graph overhead.

- [Fresh v1 run](results/verified/graph_v1/180fba46b3a145e2b5f19ccced278f664e2c4a06b5b792f1605f8fd07c3d87be/20261014T042408031523Z-f93405a4/result.json).
- [Fresh v2 run](results/verified/graph_v2/cdea1257f49439597adc27e2a10bd4ed99767b68c18ba5249cd777781cd789ba/20261014T042647460539Z-e9f51e44/result.json).
- Gate replay runs live under `evals/results/replay_v2/`: fixed v1 drafts and original correctness labels, never fresh generation accuracy. Initial replay also exposed three quote-validation errors; failed checks remain missing and retryable, rather than successful refusals.
- [Initial quota observations](v2_quota_waits.json), [initial wrapper](results/quota_resume_v2.txt), [node-preserving wrapper](results/quota_resume_v2_nodes.txt). Node-preserving observations are written to `v2_node_quota_waits.json` when a quota wait occurs.

The first cross-SDK heartbeat invocation failed quote validation in the sufficiency check, before any generator call (1,822 grader tokens, no generator usage). It remains an operational error, not a refusal or a successful answer. The [observed resumption wrapper](results/quota_resume_v2_observed.txt) now writes immutable per-call receipts under `evals/results/v2_call_receipts/` so the exact returned quotes can be inspected on a retry. These receipts contain parsed model outputs **before** deterministic quote validation; a parsed `passed=true` receipt alone is not a successful graph verdict. Prompts, models, graph code, and index remain frozen.

No full v1/v2 quality advantage or latency/token conclusion is established yet. [Judge review](JUDGE_REVIEW.md) records a confirmed scope false-positive and a disputed heartbeat API judgment in the fresh set. Preserve those limitations when interpreting any completed scores.

## Next course

1. Complete quota-limited comparisons and inspect gate errors and false refusals; choose gates from measured tradeoffs.
2. V2.1: preserve meaningful short code chunks. The current index drops the 28-character `python worker.py` block, making one known answer unavailable regardless of retrieval k.
3. Measure answer-bearing chunk coverage and multi-SDK coverage with a larger candidate pool and bounded context; then test lexical/hybrid retrieval if identifier misses persist.
4. Add a bounded corrective retrieval loop only for demonstrated residual failure types. Multiple agents and memory have no demonstrated need yet.

The [seven-refusal diagnosis](RETRIEVAL_DIAGNOSIS_V2.md) and [exact labels](retrieval_labels_v2.json) support that order. The short-code ingestion defect remains unfixed in the shared comparison index.
