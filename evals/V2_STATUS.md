# Evidence-gated v2: results and next course

V2 is implemented and locally verified: **66 tests pass**. It checks evidence sufficiency before unchanged v1 generation, checks claims against cited chunks afterward, refuses on negative verdicts, and retains rejected drafts and gate evidence. Errors remain operational failures. This is a research upgrade with measured abstention tradeoffs, not a demonstrated general accuracy improvement.

## Experiment boundaries

- Repaired v0/v1 baseline: `9dcd9ef`, preserved in [development results](RESULTS_VERIFIED.md) and [earlier holdout results](RESULTS_HOLDOUT.md).
- Semantic v2 implementation: frozen at `cd815e7` before authoring the [four-question confirmation set](CONFIRMATION_V2.md). Both fresh runs used the same code hashes, questions, model settings, and **14,153-chunk index**. Generation: `openai/gpt-oss-120b`; gates/judges: `openai/gpt-oss-20b`.
- Subsequent fixes: short fenced-code retention (`8dc2fae`) and deterministic recovery of source-exact quotes after simple prose formatting changes (`2f70f3f`). Prompts, schemas, model settings, and semantic decisions were not tuned. Original live results remain unchanged.
- Current index: **14,414 chunks**. All 14,153 old chunks are byte-identical; 261 short code chunks were added. The old collection remains available. [Index evidence](short_code_fix_verification.json), [post-integration verification](post_index_verification_v2.json).

## Fresh confirmation: four questions

| Metric | v1 | v2, both gates |
|---|---:|---:|
| Automated correctness | 2/4 | 3/4 |
| Answerable correctness | 1/2 | 1/2 |
| Correct private-fact refusals | 1/2 | 2/2 |
| Answerable refusals | 0/2 | 1/2 |
| Automated supported-correct answers | 1/2 | 1/2 |
| Missing eligible metrics / final generation errors | 0 / 0 | 0 / 0 |

Both answer the converter-before-codec question correctly. V2 prevents v1's unsupported private Nova timeout assertion and both refuse the private Orion key question. On the cross-SDK heartbeat question, the generator supplied the same draft in both runs; v2 rejected `RecordActivityHeartbeat` because its cited Go chunk only established `RecordHeartbeat`, and retained the draft before refusing.

The heartbeat correctness label is disputed: the question does not distinguish in-Activity from external heartbeats, and part of the judge rationale contradicts the reference. V1's private Nova assertion also received an erroneous positive faithfulness judgment. Thus both runs' automated unsupported-answer rate of zero is misleading. Original labels are preserved; [judge review](JUDGE_REVIEW.md) records the disagreements.

This set has two answerable and two private-fact questions, authored and source-checked by the coding assistant after freezing implementation. It is not an independent human or blind representative benchmark. One question changes correctness by 25 percentage points. The apparent 50% to 75% gain does not establish broad superiority.

Raw evidence: [v1 run](results/verified/graph_v1/180fba46b3a145e2b5f19ccced278f664e2c4a06b5b792f1605f8fd07c3d87be/20261014T042408031523Z-f93405a4/result.json), [v2 run](results/verified/graph_v2/cdea1257f49439597adc27e2a10bd4ed99767b68c18ba5249cd777781cd789ba/20261014T042647460539Z-e9f51e44/result.json). Every eligible metric is scored. The current index returns exactly the same ordered chunks, text, and metadata for these four questions; this is a retrieval check, not a new native evaluation.

## Component ablations: ten fixed v1 drafts

This regression replay reuses saved v1 answers and original correctness labels. It measures rejection behavior, not fresh end-to-end generation accuracy. The [original native replay](results/replay_v2/2b50de398c1691e9b31b35d0e076907cffcbbe9ab664cf2a71be68a6b8b457c3/result.json) ended with coverage 10/10 for v1, 9/10 for sufficiency, and 8/10 for support and both. Three checks failed because quotes collapsed newlines, omitted bold, or rendered a Markdown link label.

The formatter fix restores exact source spans for those changes while preserving inline code, document IDs, and each recorded verdict/reason. Changed numbers, API names, URLs, and code still fail validation. Fenced/indented code requires literal quotes; complex Markdown recovery is deliberately unsupported. [Offline revalidation](results/revalidated_v2.json) applies the new validator to the recorded native outputs with exact receipt/input checks. All three missing stages now validate; previously accepted stages, all four confirmation outputs' gate verdicts, and eight recorded calibration controls remain unchanged. **No new model calls or correctness judgments occurred during revalidation.**

The completed revalidation gives:

| Fixed-draft variant | Scored | Correct, original labels | Answerable refusals | Private-fact answers | Source-audited supported-correct | Source-audited unsupported answers |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 10/10 | 6/10 | 2/8 | 1/2 | 4/8 | 2/10 |
| Sufficiency only | 10/10 | 6/10 | 4/8 | 0/2 | 4/8 | 0/10 |
| Support only | 10/10 | 6/10 | 2/8 | 1/2 | 4/8 | 2/10 |
| Both | 10/10 | 6/10 | 4/8 | 0/2 | 4/8 | 0/10 |

Source-audited columns use the coding assistant's explicit cited-claim review stored in the artifact, not independent human labels or substituted automated faithfulness scores. The two unsupported answers are private Acme configuration inferred from a public sample, and a correct retention explanation whose cited chunk supports the deletion remedy but omits the causal timer claim. Refusals make no factual claims. The Activity Execution draft has supported facts but answers the wrong definition; support-only accepted it too.

Sufficiency catches missing evidence and scope here. Support-only misses all three semantic problems above despite passing synthetic controls. Adding support provides no incremental fixed-draft benefit in this sample; it also rejected the disputed heartbeat draft in fresh confirmation. Keep both as the implemented research reference, but compare sufficiency-only on new, independently reviewed questions before deciding whether the extra check earns its cost. These inspected regression rows must not become a new blind holdout.

Reproduce the offline audit, including provenance hashes and assert-based checks:

~~~sh
LANGSMITH_TRACING=false .venv/bin/python evals/results/revalidate_recorded_v2.txt
~~~

## Usage and latency

Fresh v1's four final graph outputs report **6,917 generator tokens**. Fresh v2 reports **3,244 generator plus 11,697 gate tokens**, with generation skipped for both private-fact questions. An earlier failed heartbeat gate used another 1,822 tokens, retained in raw history and excluded from those final-output totals. Evaluation judges, other failed/retried calls, calibration, and earlier experiments are outside these counts. Different models have different billing; token totals are not a monetary cost comparison or billing ledger.

Observed mean graph time is 4.625 seconds for v1 and 695.048 seconds for v2. V2's time includes long provider quota waits, so it cannot estimate intrinsic gate overhead. The wrapper obeyed provider retry-after delays and preserved completed nodes without switching models. [Call receipts](results/v2_call_receipts/), [wrapper](results/quota_resume_v2_observed.txt), [quota observations](v2_observed_quota_waits.json) retain the evidence.

For the conditional fixed-draft replay, selected final gate attempts report 18,260 tokens for sufficiency-only, 10,959 for support-only, and 23,192 for both. These are retrospective sums of applicable recorded stages; the original replay ran stages independently. They exclude v1 generation and earlier attempts, and are not measured full-workflow cost or latency.

## Recommended next version

1. **Measure bounded expansion within a retrieved section.** The repaired `python worker.py` chunk is indexed but still absent from top five; it ranks 50th in a 100-candidate diagnostic. Its exact source/heading already appears in top five. That section totals only five chunks and 1,434 characters, including the command. Expand from those anchors with explicit context limits and stable citations, then compare answer-bearing coverage, supported correctness, false refusals, and token use on development data.
2. **Measure both-SDK coverage.** The [seven-refusal diagnosis](RETRIEVAL_DIAGNOSIS_V2.md) shows every selected refusal omitted a necessary fact, including three with perfect document-level recall. Preserve chunk-level labels. Test lexical/hybrid retrieval only if bounded context still misses identifiers or a second SDK.
3. **Confirm the selected retrieval change on new reviewed questions.** Keep the old four-question confirmation and ten-question regression artifacts fixed. Broaden source review and judge adjudication; include both answerable and private-scope cases.
4. **Then consider one corrective retrieval retry** for demonstrated residual failures, with a strict attempt/context budget. Agents and memory have no demonstrated need for this task yet.

No bounded section expansion, hybrid retrieval, corrective loop, private-data ACLs, deployment, or Windows runtime verification is claimed by this release. The installed v2's broader quality on the upgraded index remains unmeasured. [Completion evidence](V2_COMPLETION.md) distinguishes implemented requirements from the next experiments.
