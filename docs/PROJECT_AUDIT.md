# Project audit — 14 October 2026

Historical initial audit. For current repairs, verification and rating, see the [v2.1 scorecard](../evals/V21_SCORECARD.md). Findings below describe the audited commit and remain unchanged as evidence.

Audited application commit: 078d185. Local corpus commit: 5b56ddca7d409a82f2d74e21f20edf35f29ad483.

**Score: 5.5/10 as the research/learning prototype described in the design.** The small graph architecture and baseline experiment are sound. Evaluation integrity and ingestion fidelity need repair before the comparison table can support strong upgrade claims.

This assesses the checked-out implementation, not the capabilities of the model that helped author it. Scores below are engineering judgments, not measured model benchmarks. Planned features are separated from defects.

| Area | Score | Weight | Reason |
|---|---:|---:|---|
| Architecture and scope | 8/10 | 20% | Small modules, shared graph contract, explicit baseline; avoids premature orchestration |
| Ingestion and retrieval | 5/10 | 15% | Useful metadata and real persisted index; code corruption and unsafe rebuild behavior |
| Evaluation validity | 4/10 | 25% | Bucketed references and separate metrics; stale checkpoints and misleading metric definitions |
| Testing | 4/10 | 15% | Five passing checks; central evaluation and refusal contracts are uncovered |
| Reproducibility and runtime reliability | 5/10 | 15% | uv lock and resumable runs; no experiment fingerprints, mutable corpus, repeated initialization |
| Documentation | 8/10 | 10% | Clear design and journal; some claims exceed the available evidence |

## What the project actually does

- Temporal Markdown/MDX files → cleaning → heading/character chunking → local BGE embeddings → persisted Chroma.
- graph_v0: question → Groq model → answer, with no retrieval.
- graph_v1: question → retrieve five chunks → Groq model → answer.
- Evaluation: 40 references, LLM correctness/faithfulness judges, source-path retrieval matching, deterministic refusal matching, JSONL checkpoints, Markdown comparison.
- v2/v3, supervisors, specialized agents, conversational memory, routing, hybrid search, ACL enforcement, and a user-facing application are not implemented.

Calling the current implementation a **versioned RAG evaluation prototype** is more precise than presenting it as an implemented multi-agent system. Keeping v1 small was a good decision; missing future phases are not bugs.

## Verification performed

- All 5 existing tests passed with network-dependent model downloads disabled and LangSmith tracing disabled:

~~~sh
LANGSMITH_TRACING=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest -q
~~~

- 14 additional temporary assertion-based probes confirmed ingestion/evaluation failures; a separate probe confirmed limited runs overwrite full aggregates. These used fake provider calls and temporary result/index directories.
- Fresh local chunking produced 9,765 chunks from 762 source files, matching the existing SQLite index counts.
- Golden data has 40 distinct questions, correct declared bucket counts, and no missing cited source files.
- Recomputed bucket totals from committed partial results and checked the published aggregate numbers.
- Inspected representative source passages, including the PHP multihop reference and Go/TypeScript permission differences.
- No live Groq generation or judging, external browsing, credential inspection, fresh installation, destructive corpus fetch, or production-index rebuild was performed.

## Priority 1 — repair before measuring upgrades

### 1. Evaluation checkpoints can silently reuse obsolete results

**Evidence:** evals/run_eval.py:46–58, 92–102; evals/compare.py:30–38. Reproduced with an unchanged question and changed reference/source: graph invocation was skipped and the old verdict reused.

Cache identity is only graph module filename plus question text. Changes to graph code, prompt, shared llm/retrieval helpers, reference answer, source labels, corpus, embedding model, judge, or model settings do not invalidate results. Even compare.py --run calls the same checkpoint-resuming runner; it does not guarantee new inference.

**Impact:** an upgrade can appear to have been evaluated without actually running. Separate graph files do not solve changes in shared helpers.

**Small fix:** fingerprint all relevant run inputs, scope checkpoints to that fingerprint, and provide an explicit fresh-run path. Reject cached aggregates from incompatible runs.

### 2. Re-ingestion appends duplicate/stale chunks

**Evidence:** ingest.py:99–106. In a temporary real Chroma collection, indexing the same single chunk twice produced two stored documents.

No stable IDs, replacement, or deletion handles repeated runs or changed/deleted source files.

**Impact:** rebuilding can change top-five diversity and retain outdated content. The existing count of 9,765 does not itself demonstrate that the current index was repeatedly ingested.

**Small fix:** make rebuilding explicit and replace the collection safely, or use stable IDs with deletion of obsolete chunks. Test two runs and a deleted source.

### 3. Heading splitting strips code indentation

**Evidence:** ingest.py:48–65. The installed MarkdownHeaderTextSplitter transforms a fenced Python function with an indented return into an unindented body. Fresh chunks from develop/python/integrations/google-genai.mdx show the same damage.

**Impact:** retrieved Python examples can be invalid even though clean_mdx preserves triple-backtick blocks.

**Small fix:** preserve code whitespace throughout the complete chunking pipeline; test the final chunks, not only the cleaner.

### 4. Cleaner removes inline generic type parameters

**Evidence:** ingest.py:26, 35–40. Actual corpus examples become CompletableFuture instead of CompletableFuture<R>, and Arc instead of Arc<Self>. Inline List<String> becomes List.

**Impact:** technically meaningful type information disappears before embedding.

**Small fix:** protect inline code as well as fenced code before JSX cleanup. Map<String, String> happens to survive this regex; not every generic is affected.

### 5. “Recall@5” is an any-source hit, not multi-source recall

**Evidence:** evals/run_eval.py:127–129. A question requiring a.mdx and b.mdx gets 1.0 when only a.mdx is retrieved.

**Impact:** reported 1.0 multihop recall does not establish retrieval of all needed evidence.

**Small fix:** report source recall as retrieved expected sources / expected sources, plus an all-required-sources success metric. Keep any-source hit rate only under an accurate name.

### 6. Empty retrieval is excluded from retrieval scoring

**Evidence:** evals/run_eval.py:117–129. The recalled field is written only when docs is truthy. A temporary graph returning no documents received null recall instead of zero.

**Impact:** an answerable question with failed retrieval disappears from the denominator. Preserve N/A deliberately for v0; retrieval-enabled graphs should record a miss.

**Small fix:** declare whether a graph uses retrieval, and score every answerable row for retrieval-enabled versions.

### 7. “Unjudged: 0” hides missing faithfulness judgments

**Evidence:** evals/run_eval.py:119–125, 139–151; evals/results/graph_v1.partial.jsonl:22.

The external-storage multihop row has a correctness verdict but no grounded verdict. The published 0.839 is 26/31; there are 32 answerable questions. Unjudged counts only missing correctness, so still reports zero.

**Impact:** the journal's claim that every shrunken judgment denominator is visible is false.

**Small fix:** publish eligible/scored/missing counts per metric, including faithfulness, rather than one ambiguous counter.

### 8. Refusal detection accepts fabrication and rejects valid refusal wording

**Evidence:** evals/run_eval.py:34–36, 105–108. Both behaviors reproduced.

- “I don't know for sure, but the price is $999.” passes as a correct refusal.
- “The provided context does not contain that information.” fails.

**Impact:** refusal rate cannot be equated with fabrication rate. The claimed reduction from 3/8 fabrications to 1/8 is a count of string-check failures, not independently verified fabrication.

**Small fix:** enforce the exact refusal contract or return a structured answer/refusal status, then verify that refusal carries no additional factual answer.

### 9. Evaluation evidence is not retained

**Evidence:** evals/run_eval.py:99–129. Checkpoints retain questions, buckets, and verdicts; they omit generated answers, retrieved source IDs/content, and judge inputs or explanations.

**Impact:** the reported errors cannot be independently replayed from committed artifacts. Possible external traces are not a portable substitute, and were not inspected.

**Small fix:** retain the answer, retrieved stable IDs and source metadata, run fingerprint, judge outcome/error, and per-metric eligibility.

### 10. Several “direct” questions are under-specified

**Evidence:** evals/golden.jsonl:3, 5, 9–11.

Examples: “What command is used to start the Worker?”, “What is the task queue name used when executing the workflow?”, and “How often does the dashboard poll the web service?”

These require an unstated sample, SDK, or guide. The graph receives only the question, not its source label. The corpus contains many workers, queues, and dashboards.

**Impact:** a legitimate alternative answer or clarification can be marked wrong, confusing question ambiguity with retrieval failure.

**Small fix:** name the guide/sample/SDK in each question. Keep intentionally ambiguous questions in a separate bucket with appropriate expected behavior.

### 11. A “multihop” reference is fully supported by one source

**Evidence:** evals/golden.jsonl:26, question numbered 25 in REVIEW.md; corpus/docs/develop/php/workflows/message-passing.mdx:638–644.

The message-passing document states both the WorkflowInit-before-handlers behavior and why constructors help handlers access input. The second citation is unnecessary.

**Impact:** the journal's claim that this regenerated bucket consistently requires both documents is not supported.

**Small fix:** test each multihop row against each individual source and replace rows that do not actually require multiple evidence sources.

### 12. Exact-path ground truth penalizes valid alternate evidence

**Evidence:** evals/run_eval.py:127–129; eight jargon references point only to glossary.md. docs/journal.md:234–250 already acknowledges the issue.

**Impact:** jargon recall of 2/8 cannot yet be interpreted as six genuine retrieval failures. Correctness of 8/8 does not resolve whether alternative retrieved evidence or model memory supplied the answer.

**Small fix:** review the retrieved evidence and label acceptable alternatives/evidence groups before using this metric to justify hybrid retrieval.

## Priority 2 — reliability and data-quality repairs

### 13. Limited evaluation overwrites a full result

**Evidence:** evals/run_eval.py:81, 89, 153. Reproduced: a full two-question result was replaced by n=1 after a limited run of the same version.

**Small fix:** store exploratory/limited runs separately and prevent compare.py from presenting them as full phase-gate results.

### 14. Failed judgments are never retried on resume

**Evidence:** evals/run_eval.py:101–102, 131–133. A row with missing grounded was checkpointed and remained missing on the next run.

**Small fix:** retain generation/retrieval once, but retry incomplete metric work separately.

### 15. A torn final checkpoint record prevents recovery

**Evidence:** evals/run_eval.py:55–58, 132–133. A simulated truncated last JSONL line raised JSONDecodeError.

**Small fix:** recover a demonstrably incomplete final append, while failing clearly on corruption elsewhere. Write aggregate JSON atomically.

### 16. Each generation call gets its own rate limiter

**Evidence:** llm.py:34–54; graph_v0.py:22; graph_v1.py:31. Two get_llm calls produced separate InMemoryRateLimiter objects.

**Impact:** there is no shared process-level request budget for generation. Judges keep their own constructed chains; limits are not coordinated across all same-model calls.

**Small fix:** reuse models and a per-model limiter. Keep TPM limitations explicitly separate from RPS throttling.

### 17. Retrieval reconstructs embedding infrastructure per question

**Evidence:** graph_v1.py:27 → retrieval.py:11 → ingest.py:91–95 → ingest.py:84–88.

Each retrieval constructs a new HuggingFaceEmbeddings client and Chroma wrapper.

**Impact:** avoidable repeated model initialization and connection work; exact latency penalty was not benchmarked.

**Small fix:** reuse the existing embedding/vector-store/retriever objects within a process, with deliberate invalidation on index changes.

### 18. Corpus fetching is destructive and does not pin the snapshot

**Evidence:** fetch_corpus.sh:4–6 deletes corpus before cloning current upstream HEAD.

**Impact:** local corpus edits can be lost; a clone failure leaves no previous corpus; later setup may use a different corpus against old references and results.

**Small fix:** pin the revision, download/check it before replacement, and guard locally modified corpora.

### 19. Corpus and index paths depend on the working directory

**Evidence:** ingest.py:18–19; test_graph.py:42.

Launching from another directory can look for a different corpus/index; an empty corpus is not rejected by load_chunks/build_index.

**Small fix:** resolve project paths from the module location and fail clearly for missing corpus or absent/empty index.

### 20. The drafter requests SKIP but stores it as a question

**Evidence:** evals/draft_golden.py:70–71, 117–122. Any non-null QA object is appended, including question="SKIP".

**Small fix:** discard the sentinel, reject empty/duplicate questions, and report accepted counts against requested counts.

### 21. Draft generation can silently produce too few candidates

**Evidence:** evals/draft_golden.py:105–131. Each bucket has exactly n attempts; errors or failed pair selection reduce the count, but output still succeeds.

**Small fix:** bounded extra attempts and explicit incomplete status. The current golden set itself has the intended 40 rows.

### 22. The permission reference flattens SDK-specific differences

**Evidence:** evals/golden.jsonl:22; Go external-storage source:42–43; TypeScript external-storage source:39–40.

Go says storing also needs read access. TypeScript says retrieval-only components need no write access and “the reverse is also true.” The golden answer concatenates both into a universal statement.

**Impact:** the expected answer is ambiguous about whether store-only access requires read.

**Small fix:** describe the two SDKs separately or reconcile the corpus inconsistency before scoring this question.

## Coverage and presentation gaps

These are missing safeguards or limits, rather than proven live exploits or proof that the prototype must become a production service.

### 23. Tests do not exercise the central behavior

**Evidence:** test_graph.py:39–46 checks only that graph.invoke exists; no graph invocation, refusal contract, evaluation cache, metric, or rebuild test exists. The design spec:175–179 explicitly promised an unanswerable/refusal assertion.

**Small fix:** a few offline behavioral tests around the failures above. Keep the local retrieval integration test separately identifiable.

### 24. Prompt and judge data lack an enforced trust boundary

**Evidence:** graph_v1.py:15–23, 31–34; evals/run_eval.py:112–123.

Question, retrieved passages, and instructions are interpolated into a single message string. The judges similarly mix answer/context text with their instructions. A source or answer can contain competing instructions.

**Small fix:** put instructions in system messages, label supplied text as untrusted data, and test adversarial passages and answers. Message roles reduce ambiguity but do not by themselves eliminate prompt injection. No live exploit was attempted.

### 25. Model-output citations are neither required nor validated

**Evidence:** retrieval.py:14–20 adds source labels, but graph_v1.py:15–23 does not require cited claims, and generation returns only text.

**Upgrade option:** retain the existing text interface and add separately inspectable source evidence. If the product promises citations, validate that cited IDs were retrieved and support the relevant claims.

### 26. Small, repeatedly used test set has no held-out confirmation

**Evidence:** evals/golden.jsonl has 40 rows; unanswerable has eight; comparison artifacts show one recorded evaluation per implemented version.

One total question is 2.5 percentage points; one refusal question is 12.5 points. Future tuning on the same rows risks fitting this set. Same model family participates in drafting, generation, and judging, so independent calibration matters.

**Small fix:** reserve a blind holdout, calibrate a small judge sample manually, and report per-bucket counts/uncertainty. Repeated provider runs were not performed in this audit.

### 27. Low baseline performance does not prove absence of memorization

**Evidence:** docs/journal.md:219–222; graph_v0.py:3–4; README.md discussion of v0.

A low score on these exact questions can also reflect under-specification, reference mismatch, refusal wording, or limited model capability. Retrieval gains are evidence that context helps; they do not establish clean training provenance.

**Small fix:** qualify the claim and use private/synthetic controlled facts if measuring contamination is essential.

### 28. Default tracing needs an explicit data-sharing choice before private corpora

**Evidence:** .env.example:10–13 enables LangSmith tracing.

This project currently uses public documentation; no credential leak was found or alleged. If upgraded to internal/tenant data, prompts and retrieved content can become external trace data when tracing is configured.

**Upgrade requirement:** document that data flow, make tracing deliberate, and add redaction/access controls appropriate to the actual data.

### 29. ACL metadata is a placeholder, not access control

**Evidence:** ingest.py:76–78 marks every chunk permitted_roles="all"; retrieval.py:11 does not filter roles.

This is explicitly deferred by the design, so it is not a broken promise for the current public corpus.

**Upgrade requirement:** if introducing private sources, enforce identity-based filtering before any content reaches the generator or tracing.

### 30. Planned v2 bundles changes that need separate attribution

**Evidence:** design spec:109–115 proposes grading, rewriting, groundedness, refusal, and hybrid retrieval together.

A single v1-versus-v2 comparison cannot identify which component produced a gain.

**Upgrade option:** change one factor at a time or add small ablations when making component-specific claims. Do not build agents solely to match the repository name.

## What the committed results support

The arithmetic below matches saved verdicts; generated outputs were not retained, so this audit cannot independently rejudge them.

| Metric | v0 | v1 | Interpretation |
|---|---:|---:|---|
| Overall correctness | 17/40 | 32/40 | Includes refusal string matches as correctness on eight questions |
| Answerable correctness | 12/32 | 25/32 | Useful initial evidence that retrieved context helps |
| Faithfulness | N/A | 26/31 | One missing judgment; not 32 fully judged answers |
| Any-expected-source hit | N/A | 22/32 | Current metric labelled Recall@5; does not require all multihop sources |
| Refusal string match | 5/8 | 7/8 | Not independently verified hallucination/fabrication rates |

v1 answerable bucket correctness: direct 8/12, jargon 8/8, multihop 7/8, ambiguous 2/4. Multihop faithfulness is 4/7 scored, with one missing judgment. That is a more important signal to investigate than the misleading perfect multihop source-hit rate.

## Smallest useful upgrade order

1. Repair run identity, evidence retention, and metric denominators; preserve the historical results as historical.
2. Preserve code during ingestion and make index rebuilding repeatable; produce a new explicitly versioned index.
3. Repair ambiguous/multihop/reference labels and refusal scoring; reserve held-out questions.
4. Rerun v0/v1 against the repaired setup and record complete evidence.
5. Choose the next change from actual failures: lexical/hybrid retrieval for demonstrated identifier misses, or query rewriting for demonstrated phrasing misses. Evaluate them separately.
6. Add bounded corrective loops or multiple agents only when the repaired evaluation shows a need.

No application fixes were applied as part of this audit. Existing source files, golden data, and historical result artifacts were preserved. The working tree already contained a .serena/project.yml modification at the initial status check; this audit did not attempt to revert it.

## Repair follow-up — 14 October 2026

The sections above preserve the original assessment and original score. The user subsequently authorized repairs. Implementation changes and verification are tracked below; remaining experimental limits are not represented as eliminated risks.

| Finding | Repair / disposition | Verification |
|---|---|---|
| 1 | Fingerprinted inputs and isolated attempts; --run forces fresh inference | test_evals: resume, changed reference, and fresh-run regression; actual model/code/dependency identity assertions |
| 2 | Stable IDs and separate immutable index collections; atomic manifest publication | test_ingest: repeated build, source deletion/replacement, failed build |
| 3 | Whitespace-preserving syntax/header splitter and size splitter | test_ingest: final code chunk retains nested Python indentation |
| 4 | Protect inline code and both fence styles during cleanup | test_ingest: generic types and MDX imports |
| 5 | Fractional evidence-group recall and separate all/any-source rates | test_evals: one of two groups is 0.5, not 1.0 |
| 6 | Empty retrieval is a miss for retrieval-enabled graphs; v0 declares N/A | test_evals: empty retrieval and denominator |
| 7 | Eligible/scored/missing counts per metric | test_evals: missing faithfulness visible and incomplete |
| 8 | Whole-answer refusal contract | test_evals: appended fabrication rejected; normalized exact refusal accepted |
| 9 | Retain answers, chunks, metadata, citations, judge inputs/outputs/reasons/errors | test_evals: evidence serialization; new verified artifacts |
| 10 | Name SDK, sample, or guide in under-specified questions | revised golden.jsonl and REVIEW.md |
| 11 | Replace weak multihop rows with explicit cross-SDK comparisons | revised references require two separate SDK evidence groups |
| 12 | Reviewed alternate source paths within evidence groups | all eight jargon rows; alternative-source regression |
| 13 | Sample size contributes to run identity; exploratory attempts isolated | test_evals: limited run preserves full result |
| 14 | Retry missing judgments without repeating generation | test_evals: failing then recovered judge |
| 15 | Recover a torn final append; reject internal corruption; publish JSON atomically | checkpoint regression and atomic-publication failure test |
| 16 | Cached model clients and shared limiter per model | test_graph: client and limiter reuse |
| 17 | Cached embeddings, store, and retriever; new collection invalidates store selection | index tests and full retrieval integration |
| 18 | Pinned revision, staged replacement, backup, refusal of local changes | real local-Git fetch/update/dirty-checkout test; pinned production checkout check |
| 19 | Project-relative absolute paths and explicit missing/empty failures | test_ingest: changed working directory and missing corpus/index |
| 20 | Discard SKIP, empty, and duplicate drafts | test_tools: rejected sentinels and duplicates |
| 21 | Bounded replacement attempts; incomplete output cannot replace a good draft | test_tools: incomplete draft failure and preserved previous output |
| 22 | Reference explains Go versus TypeScript prerequisites separately | golden row dev-21; source comparison in REVIEW.md |
| 23 | Behavioral graph, refusal, citation, persistence, evaluation, and fetch tests | full pytest suite; graph invocation tests use fake providers |
| 24 | Separate trusted system messages and untrusted JSON data; adversarial controls | role-separation test, eight live judge controls, and three live generation controls; prompt injection is mitigated, not eliminated |
| 25 | Require retrieved citation IDs; preserve source/chunk references; judge cited context | invalid/invented citation regression and faithfulness evidence |
| 26 | Add held-out confirmation references and explicit judge controls; qualify uncertainty | holdout.jsonl and calibration.json; shared authorship/topics and small sample remain limitations |
| 27 | Correct model-only/contamination claims | README, architecture, graph_v0, historical journal/spec notices |
| 28 | Example tracing defaults off; document outbound data and preserve local preferences | .env.example; all audit/test runs explicitly disable tracing |
| 29 | Explicit public-data scope; private-data use unsupported until ACLs exist | README/architecture; no unimplemented tenant-safety claim |
| 30 | Require separate experiments or ablations before component-specific claims | README/architecture and historical design notice; no unrequested v2/agent implementation |

Local tests, calibration, rebuilt index, and live evaluation artifacts are the authoritative evidence for this follow-up. Historical result files are preserved; current metrics are published separately in evals/RESULTS_VERIFIED.md and evals/RESULTS_HOLDOUT.md. Source audit was performed by the coding assistant; independent human dataset certification is not claimed.

Verification so far: 31 local tests passed; all eight judge controls and all three generation controls passed. A repeated build of the real 14,153-chunk index preserved its manifest and IDs. The first live generation pass exposed schema-definition responses; the system prompt now explicitly requests a JSON instance, and the shared structured-output helper uses bounded parser retries. The regression covers a schema-response failure followed by a successful retry. An earlier in-flight evaluation correctly refused aggregate publication when the source code changed; its raw artifacts remain preserved.

The repaired development baseline completed 40 questions per graph with no missing judgments or generation errors: v0 correctness 0.475; v1 correctness 0.675, answerable correctness 0.594, faithfulness 0.938, source recall 0.781, all-sources success 0.719, exact refusal 1.000. These are not directly comparable to the original baseline because references, prompts, and metrics changed. Retained failures, including two correct-but-ungrounded answers, remain evidence for future model/retrieval experiments.

The first holdout pass exposed a real Groq daily token limit on its last two v1 generations. Their values stayed missing and the run was marked incomplete. A regression verifies that a provider failure is not scored and that resuming retries only the failed row. Both missing calls subsequently succeeded after honoring the provider refill window; successful rows were reused, and no values were inferred from the references. See evals/quota_waits.json.

The final holdout is complete for both graphs with no missing judgments or generation errors: automated correctness is v0 10/10 and v1 6/10; v1 answerable correctness is 5/8, faithfulness 8/8, source recall 0.812, all-sources success 0.750, and exact refusal 1/2. This small, relatively familiar-topic set does not demonstrate a retrieval advantage. It is a reason to investigate retained retrieval/generation failures on development data and validate future changes on fresh confirmation questions, not to tune to these holdout answers or claim universal improvement.

Actual-output spot-checking found a confirmed correctness-judge false-negative on dev-08: the generated answer includes the exact task-queue identifier, but the judge invents a spelling mismatch. See evals/JUDGE_REVIEW.md. Raw verdicts and automated aggregates are preserved; correcting that one label alone would yield 28/40, but this partial adjudication is not presented as a fully reviewed accuracy score. Passing calibration controls does not remove judge uncertainty. This is an experimental limitation made visible by the repaired evidence retention, not a claim that all future model or judge answers are correct.

Final verification: 31 tests passed; 100 live graph outputs across development/holdout were scored with current input fingerprints and zero missing eligible metrics. All 11 live calibration/control cases passed. The real index rebuild is idempotent; original references/result artifacts match their original Git bytes; result links resolve and git diff --check passes. This completes the current audit-repair pass, not the proposed v2/v3 product roadmap. A concrete quality limit remains: v1 fabricated MaximumAttempts=3 for an unknown private billing repository on holdout. Corrective grounding/refusal, broader independent reference/judge review, and private-data ACLs are further experiments or deployment prerequisites, not claimed capabilities of the repaired baseline.

## Subsequent v2 upgrade

The original audit and repaired baseline above are historical snapshots. The subsequent authorized upgrade implements evidence sufficiency and cited-claim support, retains rejected drafts, exposes ablations and usage/coverage, preserves short code chunks, and recovers source-exact quotes after simple prose formatting changes. Current verification is 66 passing tests and a 14,414-chunk index. Fresh native confirmation, recorded-output replay revalidation, judge disagreements, and recommended retrieval experiments are documented separately in [v2 results](../evals/V2_STATUS.md). The initial 5.5/10 score describes the original audited snapshot; it is not a new score for v2 or proof of model authorship errors.
