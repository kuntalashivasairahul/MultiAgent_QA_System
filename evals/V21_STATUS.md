# V2.1: bounded section retrieval, initial results

V2.1 is implemented as `graph_v2_1` on `codex/section-retrieval-v2-1`. **82 tests pass.** It recovers a previously missing Worker command and produces a correct cited answer in a live development regression. It does not establish a general accuracy improvement: most diagnosed evidence gaps remain, context nearly doubles, and provider rate limits blocked the fresh confirmation.

## Implemented scope

Five dense anchors remain first, in their original order. The retriever appends nearest canonical chunks from each anchor's contiguous source/heading section, processing anchors by rank. Stable IDs prevent duplicates. Results are capped at **ten chunks and 8,000 document-text characters**; additions that do not fit are skipped. Anchors exceeding the budget fail explicitly. Expansion never truncates a stored chunk or its code. The character limit excludes JSON metadata and the rest of the prompt; it is not a tokenizer budget.

Section membership and source order come from the existing chunker, cached by verified collection identity. Repeated heading paths in separate contiguous runs do not become one section. Returned additions are copied so callers cannot mutate cached evidence. The unchanged index still contains 14,414 chunks. No embedding, corpus, ingestion, semantic gate prompt, model, citation rule, refusal contract, or corrective-loop change is bundled into this version. V2's graph builder accepts a retrieval node so both versions share the same gate/generation implementation.

All original anchors remain available; early anchors can nevertheless consume the expansion budget. Expansion cannot find a section with no anchor and does not promise balanced SDK coverage. Extra context can distract a model.

## Current retrieval measurements

[Current diagnostic inputs](results/section_retrieval/f9d9edaecd10f25d344e01eae89a27f9acacb20ff7c619d02c62c32c91944ec4/inputs.json) and [retained contexts/results](results/section_retrieval/f9d9edaecd10f25d344e01eae89a27f9acacb20ff7c619d02c62c32c91944ec4/result.json) cover all 40 development questions, including 32 answerable questions. No generation or judging is involved in this comparison.

| Measurement | Dense five | Bounded section context |
|---|---:|---:|
| Selected diagnostic facts present | 3/11 | 5/11 |
| Fully covered diagnostic questions | 0/7 | 1/7 |
| Mean required-source-group recall, 32 answerable questions | 0.78125 | 0.78125 |
| All required source groups present | 23/32 | 23/32 |
| Mean document-text characters, all 40 questions | 2,656.3 | 5,219.7 |
| Mean returned chunks | 5 | 9.55 |

Maximum expanded text was 7,862 characters. All 40 contexts satisfy both budgets, retain every original anchor, and preserve canonical text/metadata. Source recall is unchanged because expansion stays in anchored sections. This table's fact labels are selected coding-assistant annotations from the existing seven-refusal diagnosis, not exhaustive or independent ground truth.

The two newly recovered facts are `python worker.py` and Python's `workflow.continue_as_new` call in the cross-SDK question. The latter still lacks its Java fact. Java API sections, the dashboard polling fact, Go storage permissions, Java suggested-new-run API, and Python ABANDON options remain missing in their respective diagnosed contexts. Source-level recall alone conceals these gaps.

Reproduce the current retrieval-only measurement:

~~~sh
LANGSMITH_TRACING=false GROQ_MAX_RETRIES=0 uv run python evals/diagnose_sections.py
~~~

## Live development regression

The implementation was first frozen at `6594c2a`. Both graphs then ran the known one-question Worker-command regression with matching source hashes, index and model settings. SDK retries were set to zero in both; generation used `openai/gpt-oss-120b`, gates/judges used `openai/gpt-oss-20b`.

| Known development question | V2 | V2.1 |
|---|---|---|
| What command starts the Python Worker in the Celery migration guide? | `I don't know.`; sufficiency rejected the missing command | `python worker.py`; both gates passed; citation ID 8 identifies the actual command chunk |
| Automated correctness / faithfulness | False / True, refusal has no factual claim | True / True |
| Reported generator tokens | No generator call | 2,355 |
| Reported gate tokens | 1,981 | 3,506 |
| Observed graph wall time | 5.403 s | 10.341 s |

The answer and citation were source-checked by the coding assistant. This is a known regression chosen to test the diagnosed retrieval defect, not fresh confirmation or a representative score. Token counts exclude evaluation judges and are not a monetary billing comparison; the workflows took different branches. One observation cannot estimate general latency or cost.

Raw evidence: [v2 probe](results/verified/graph_v2/6e949119ed12ba6520ef404d9109096cf0351f7d3a9895950a995acf28ee1008/20261014T125517419253Z-61e4b687/result.json), [v2.1 probe](results/verified/graph_v2_1/9df8e11185ead4464c7595203c660fba6ac61d8d9c158be5bf8cc53e688944b6/20261014T125526393552Z-9c5a389c/result.json).

## Fresh confirmation is incomplete

Three questions were authored after the initial freeze: two answerable code/API cases and one unknown private setting. [Protocol](CONFIRMATION_V21.md), [dataset](confirmation_v21.jsonl), [all initial attempts](results/v21_native_initial.json).

V2 completed one graph invocation and received `RateLimitError` on two. V2.1 received `RateLimitError` on all three. Missing outputs remain operational errors, not refusals. The sequential quota-limited attempts cannot support an accuracy, refusal, grounding or latency comparison. Do not interpret the raw aggregate over v2's single scored row as its three-question accuracy.

Preserved incomplete attempts: [v2](results/verified/graph_v2/138ff0f53481d0e4e6e5b6a4e2b33a451b8d56eb6ccd471a55f85eb142cb8d86/20261014T125544936648Z-07281bb1/result.json), [v2.1](results/verified/graph_v2_1/583cceb2a7e337504bbe79a799fa4e4b1bf14d6b0cbb12eec122f6632610dc57/20261014T125604465582Z-fd3c4435/result.json). Existing v2 confirmation and regression datasets were not modified. This small new set also has shared authorship and no independent human review.

## Post-study cache isolation and verification

Final review found that returning canonical cached `Document` objects allowed a caller to mutate later queries' evidence. A regression reproduced it; added chunks now return independent copies. **82 tests pass** after that fix. All 40 development contexts remain identical in ID, text and metadata to the initial implementation's contexts. The current Worker probe context exactly matches the saved live inputs.

The live study still describes `6594c2a`, before the output-copy fix. [Final local verification](results/v21_local_verification.json) binds current source hashes, unchanged index/gate semantics, preserved earlier datasets, matching paired native inputs and identical contexts. This is local compatibility verification, not a new native study. The copy fix changes code fingerprints: evaluating current code creates a new identity rather than silently reusing the old paid answers. Resuming an old attempt requires matching frozen source, index and settings.

## Next course

1. Complete a paired, reviewed confirmation when provider quota is available, preserving the current results and missing-work boundaries. Broader supported correctness, false refusals and actual token tradeoffs remain unmeasured for this version.
2. Use the six still-incomplete diagnosed contexts to compare a larger, SDK-diverse candidate pool under the same context budget. Separate wrong-heading misses from missing-source misses. Test lexical retrieval for demonstrated remaining identifier misses.
3. Add a corrective retrieval retry only after those comparisons identify what a retry should change. Hybrid search, query rewriting, agents, memory and private-data access control remain outside this initial version.

The [initial plan](V21_PLAN.md) is implemented and measured at the retrieval level; its conditional fresh native comparison remains rate-limited. This milestone starts the next version without claiming a passed broad quality gate.
