# Architecture

## Corpus and index

CORPUS_REVISION pins public Temporal documentation. fetch_corpus.sh stages a checked-out revision before replacement, refuses local changes, and preserves the previous checkout. Corpus/index paths resolve from the project directory, independently of the launch directory.

~~~text
Markdown/MDX → protected inline/fenced code → ESM/JSX cleanup
             → whitespace-preserving Markdown syntax/header splitting
             → 1200-character chunks, 180-character overlap
             → pinned BGE-small, CPU, normalized
             → fingerprinted Chroma collection → atomic manifest
~~~

The lightweight cleaner leaves arbitrary JSX expressions as text; it does not evaluate MDX. Large code blocks may span size-bounded chunks, with indentation preserved. Stable chunk IDs derive from source, headings, and text. Metadata contains source, title, headings, chunk_id, and the public-only placeholder permitted_roles=all.

The manifest binds source hashes, pipeline code, dependency lock, embedding revision, collection, chunk count and a canonical text/metadata digest. Existing IDs allow an interrupted build to resume only if their content matches canonical records. Rebuilding is idempotent. Source additions/edits/deletions select a distinct collection; old snapshots remain recoverable. Readers require a current, complete manifest and validate stored text/metadata on first opening the immutable snapshot in each process. This detects accidental content corruption; embedding coordinates and malicious local filesystem changes are outside that boundary. Cached embeddings/stores/retrievers avoid per-question initialization; a newly published collection selects a new store/retriever.

## Graph contract

Every graph_vN module exports graph and USES_RETRIEVAL; retrieval-enabled modules also declare RETRIEVAL_K. graph.invoke accepts a non-empty question and returns generation, documents, and citations.

~~~text
v0: START → answer → END
v1: START → retrieve → generate → END
v2: START → retrieve → sufficiency → generate → support → END
                          ↓ insufficient          ↓ unsupported
                       refusal                 refusal + retained draft
v2.1: same v2 graph with bounded hybrid/SDK/section retrieval
v3: START → initialize → retrieval → reasoning → judge → finish → END
                          ↑                       ↓
                          └──── one quality retry ┘
~~~

v0 measures model-only answering, not training-data provenance. v1 uses a system instruction and JSON-encoded untrusted question/documents in a human message. Structured output contains answer text and numeric citation IDs. Non-refusal answers must cite actually retrieved IDs; refusals must have no citations. Empty retrieval refuses without a provider call. Invalid citations fail explicitly.

Message separation and adversarial controls reduce instruction confusion; they do not eliminate prompt injection. Citation-ID validity does not prove semantic support. This prototype has public data and no authentication or tenant boundary. Private-data ingestion is unsupported until identity-aware retrieval filtering and trace policy are implemented/tested.

V2 imports v1 retrieval/generation unchanged and extends QAState locally. Sufficiency requires evidence for all parts of the exact question; public samples do not establish private configuration. Support sees only cited chunks with their original IDs and requires every answer claim to follow from them for the requested scope. Positive verdicts require checked quotes. Evidence JSON preserves Unicode characters. The validator restores simple whitespace, bold, and link-label formatting to literal source spans, preserving inline code and IDs. Formatting recovery searches contiguous prose outside fenced/indented code; code requires literal matching and spans cannot bridge code blocks. Nested Markdown fences conservatively stay literal. It rejects changed facts and unsupported formatting. Invalid verdicts receive up to three validation attempts with the original evidence and untrusted failure feedback; rejected verdicts remain in the audit. A valid semantic negative is never retried to seek a positive. Persistent validation failures and grader outages propagate as operational failures. Audit fields reset on retrieval; support is skipped after a generator refusal. Single-check variants are ablations, not extra production workflows. These are prompt requirements and deterministic quote checks, not a guarantee that the grader enforces semantic support correctly.

## Evaluation

V2.1 fuses up to 100 dense and 100 positive-scoring TF-IDF candidates with reciprocal rank constant 60 and lexical weight 2. Text normalizes camelCase and punctuation for identifier matching. Explicit SDK mentions add filtered dense-20/lexical-100 pools, reserving up to two candidates per SDK round-robin within six anchors. It then appends nearest chunks round-robin within each anchor's contiguous canonical source/heading section, and fills remaining space from global candidates. Stable IDs deduplicate evidence; output is capped at 12 chunks and 8,000 text characters. Metadata/prompt overhead is outside that text limit and is measured separately. Cached lexical/section data are keyed by verified collection; returned evidence is copied. SDK recognition is heuristic and does not infer unspecified languages. The former section-ten policy remains a development control. [Current scorecard](../evals/V21_SCORECARD.md) separates retrieval coverage from native answer quality; [initial results](../evals/V21_STATUS.md) retain the earlier policy's evidence.

V2/v2.1 evaluation uses a synchronous SQLite graph checkpointer with a question-hash thread ID. Pending execution resumes with the same thread; a complete saved graph result can recover an interrupted answer write. SQLite transactions serialize attempt ownership. Persisted-attempt graph and judge callbacks/time accumulate, but unreported provider work and lost writes remain outside those totals. SQLite recovery state is local and ignored by Git. JSONL answers and verdicts remain portable and survive aggregation failures. New installs use GPT-OSS-120B generation and separately calibrated Qwen3.8-27B grading; actual environment values are fingerprinted. Grading remains fallible, including semantic scope/coverage errors despite valid quotes.

The 40 development references and original 10-question confirmation specify required evidence groups, with reviewed alternatives inside groups. The original confirmation is now a regression set. Current development defaults to the versioned pricing correction (33 answerable, seven unanswerable); historical references remain explicitly selectable. The selected final confirmation has 12 questions authored and source-reviewed after implementation freeze `b024062`, in `confirmation_prose_v21.jsonl`. Three earlier replacement sets were withdrawn before native execution because implementation changed. Source audit is by the coding assistant, not independent human certification. Shared authorship and correlated Temporal/SDK topics limit generalization; this is not a blind external benchmark. Comparison reports use content-addressed snapshots, preserving earlier reports.

| Metric | Meaning |
|---|---|
| correctness | Question/reference/answer judge; whole-answer refusal for unanswerable rows |
| answerable_correctness | Correctness restricted to answerable questions |
| faithfulness | Answerable questions only: every factual claim supported by cited chunks, or retrieved chunks without citations; refusals count as grounded |
| recall_at_k | Fraction of required evidence groups retrieved, accepting listed alternatives |
| all_sources_rate | All evidence groups retrieved |
| any_source_rate | At least one evidence group retrieved |
| refusal_rate | Whole answer matches the exact refusal contract; not a fabrication classifier |
| false_refusal_rate | Canonical refusals among questions answerable in the full corpus, including cases where retrieval omitted the necessary evidence |
| supported_correct_rate | Non-refusal answers both correct and grounded, among answerable questions |
| unsupported_answer_rate | Non-refusal answers judged unsupported, including unanswerable questions |

Every metric reports eligible/scored/missing counts. v0 retrieval/faithfulness are N/A. Empty v1 retrieval counts as zero recall. Failed judgments stay absent and retryable. Generation errors remain visible and make a run incomplete. Refusals on answerable rows still undergo correctness judgment.

Runs fingerprint code, dependencies, actual model configuration, references, corpus/index, and sample size. Attempt directories retain generation, retrieval, citations, judge inputs/outputs/reasons/errors, and exact run metadata. Generation is flushed before judging. Samples and fresh attempts never overwrite full historical results. Inputs are checked again before publication.

V2 gate audits and rejected drafts are retained. Generation wall-clock time includes active retrieval, rate limits, generation and gate attempts; it excludes evaluation judges and gaps between resumptions. Graph callbacks retain provider-reported generation/gate usage, including callbacks before a later failure. Evaluation-judge attempts, usage and time are recorded separately. None is a billing ledger; missing callbacks stay unreported. Variant identity contributes to the fingerprint. replay_v2.py applies gates to frozen v1 drafts and reuses original correctness labels explicitly; it cannot establish fresh end-to-end performance.

compare.py resumes matching full runs; --run forces fresh inference. RESULTS_VERIFIED.md and RESULTS_HOLDOUT.md expose coverage and raw artifacts. Original RESULTS.md and result files remain historical. Complete metric coverage is required for a phase-gate pass, regardless of quality scores.

## Runtime and scope

Groq clients and per-model request limiters are cached. Settings are fixed when llm.py loads; restart after changing .env. SDK retries handle transient errors, including TPM limits; RPS throttling is not a token-budget limiter. Timeouts/output sizes are bounded. Judges use a separately configured model and explicit positive/negative/adversarial controls.

Duration depends on account-specific token limits and response sizes. Tracing is opt-in in the example configuration. Public prompts leave the machine through Groq, and through LangSmith when tracing is enabled.

V3 implements the quality-triggered retrieval loop through three named roles and shared typed state. Judge scores are uncalibrated rubric values; acceptance also requires a supported verdict and validated citations/quotes. One retry excludes earlier chunk IDs when seeking fresh evidence, then mixes fresh and retained context under the existing caps. Per-attempt evidence is retained, and synchronous SQLite evaluation recovery is supported. See the [v3 implementation and local runtime guide](V3_LOCAL_UPGRADE.md).

The v3 Judge receives the bounded retrieved context as untrusted background to detect contradictions and operation/scope mismatches. Positive support and literal quote IDs remain restricted to the answer's cited chunks. Legacy v2/v2.1 calls retain their cited-only input. This repairs an observed limitation of judging a plausible command in isolation; it is not a guarantee of semantic correctness. FastAPI's quality response also retains optional rejected-verdict validation audits after a successful correction.

FastAPI validates each request, starts fresh graph state and allows one active inference per application process. Health is process-only. The v3 candidate uses local Llama 3.1 8B Reasoning through loopback LM Studio and a Groq Qwen Judge; per-role backend/model/retry/rate settings are recorded. Its cloud profile uses GPT-OSS/Qwen. Experimental self-judging on local 3B/8B models failed controls. The default Judge and separate evaluation grading send public inputs to Groq; external grading settings are fingerprinted separately. Reflection, ACLs and conversational memory remain proposals; broader accuracy and deployment claims require separate evidence.
