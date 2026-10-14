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

The manifest binds source hashes, pipeline code, dependency lock, embedding revision, collection, and chunk count. Existing IDs allow an interrupted build to resume. Rebuilding is idempotent. Source additions/edits/deletions select a distinct collection; old snapshots remain recoverable. Readers require a current, complete manifest. Cached embeddings/stores/retrievers avoid per-question initialization; a newly published collection selects a new store/retriever.

## Graph contract

Every graph_vN module exports graph and USES_RETRIEVAL; retrieval-enabled modules also declare RETRIEVAL_K. graph.invoke accepts a non-empty question and returns generation, documents, and citations.

~~~text
v0: START → answer → END
v1: START → retrieve → generate → END
~~~

v0 measures model-only answering, not training-data provenance. v1 uses a system instruction and JSON-encoded untrusted question/documents in a human message. Structured output contains answer text and numeric citation IDs. Non-refusal answers must cite actually retrieved IDs; refusals must have no citations. Empty retrieval refuses without a provider call. Invalid citations fail explicitly.

Message separation and adversarial controls reduce instruction confusion; they do not eliminate prompt injection. Citation-ID validity does not prove semantic support. This prototype has public data and no authentication or tenant boundary. Private-data ingestion is unsupported until identity-aware retrieval filtering and trace policy are implemented/tested.

## Evaluation

40 development references and 10 held-out confirmation references specify required evidence groups, with reviewed alternatives inside groups. Source audit was by the coding assistant, not independent human certification. Holdout topics overlap with development; it is not a blind external benchmark.

| Metric | Meaning |
|---|---|
| correctness | Question/reference/answer judge; whole-answer refusal for unanswerable rows |
| answerable_correctness | Correctness restricted to answerable questions |
| faithfulness | Every factual claim supported by cited chunks, or retrieved chunks without citations |
| recall_at_k | Fraction of required evidence groups retrieved, accepting listed alternatives |
| all_sources_rate | All evidence groups retrieved |
| any_source_rate | At least one evidence group retrieved |
| refusal_rate | Whole answer matches the exact refusal contract; not a fabrication classifier |

Every metric reports eligible/scored/missing counts. v0 retrieval/faithfulness are N/A. Empty v1 retrieval counts as zero recall. Failed judgments stay absent and retryable. Generation errors remain visible and make a run incomplete. Refusals on answerable rows still undergo correctness judgment.

Runs fingerprint code, dependencies, actual model configuration, references, corpus/index, and sample size. Attempt directories retain generation, retrieval, citations, judge inputs/outputs/reasons/errors, and exact run metadata. Generation is flushed before judging. Samples and fresh attempts never overwrite full historical results. Inputs are checked again before publication.

compare.py resumes matching full runs; --run forces fresh inference. RESULTS_VERIFIED.md and RESULTS_HOLDOUT.md expose coverage and raw artifacts. Original RESULTS.md and result files remain historical. Complete metric coverage is required for a phase-gate pass, regardless of quality scores.

## Runtime and scope

Groq clients and per-model request limiters are cached. Settings are fixed when llm.py loads; restart after changing .env. SDK retries handle transient errors, including TPM limits; RPS throttling is not a token-budget limiter. Timeouts/output sizes are bounded. Judges use a separately configured model and explicit positive/negative/adversarial controls.

Duration depends on account-specific token limits and response sizes. Tracing is opt-in in the example configuration. Public prompts leave the machine through Groq, and through LangSmith when tracing is enabled.

Corrective loops, hybrid retrieval, reflection, ACLs, and memory remain proposals. Introduce one measured change at a time or supply ablations. Multiple agents require an actual heterogeneous task.
