# Multi-Agent Q&A / RAG System — Design

**Date:** 2026-09-01
**Status:** Approved design, pre-implementation

## 1. Purpose

Build a retrieval-augmented Q&A system over a technical knowledge base, on
LangGraph / LangChain / LangSmith.

Two goals, deliberately served by one artifact:

1. **Learning** — internalize LangGraph primitives: typed state, nodes,
   conditional edges, cycles, checkpointers.
2. **Portfolio** — produce evidence of engineering judgment, not just a
   working demo.

The artifact serving both is a **comparison table**: identical questions run
against progressively more sophisticated graphs, with retrieval and generation
scored separately. The claim "reflection reduced hallucination" is only
worth making if it is measured, and the table is the measurement.

Non-goal: building the best possible RAG system. Retrieval quality is a means
of creating interesting graph problems, not the object of study. The builder
has prior RAG experience; the unfamiliar material is orchestration and
evaluation.

## 2. Corpus

**Source:** `github.com/temporalio/documentation`, `docs/` only, shallow
sparse clone. 767 markdown/mdx files, ~892k words, ~4–5k chunks.

Selected for four properties:

- **Standalone docs repo** — clone markdown without a codebase attached.
- **Low parametric contamination** — obscure enough that the model cannot
  answer from memory. This is the property that makes evaluation meaningful;
  a corpus the model already knows produces a system that scores well
  without retrieving anything.
- **Dense jargon** — *continue-as-new*, *sticky execution*, *heartbeating*,
  *task queue*. Exact-identifier terms are where dense-only retrieval fails
  and hybrid search earns its place.
- **Genuine multi-hop structure** — workflow / activity / worker / task queue
  are mutually defining, so real questions span documents.

`docs/glossary.md` provides ground truth for jargon questions.

Contamination is asserted, not assumed — §6's v0 baseline measures it.

## 3. Stack

| Layer | Choice | Rationale |
|---|---|---|
| Runtime | Python 3.12 via uv | 3.14 is system default; torch/sentence-transformers wheels unreliable there |
| Orchestration | `langgraph` | subject of study |
| LLM | Groq, via `init_chat_model` | free tier, fast, reliable structured output |
| Rate control | `InMemoryRateLimiter` | eval runs burst hundreds of calls; throttle proactively rather than react to 429s |
| Embeddings | `BAAI/bge-small-en-v1.5`, local | 384-dim, free, no quota, fast on M4 |
| Vector store | Chroma, persisted | embed once across runs |
| Observability | LangSmith, from first commit | tracing is not a later addition |

**Explicitly deferred:** RAGAS (v2), `rank_bm25` (v2), cross-encoder reranker
(only if evals show jargon misses), multi-provider fallback (only if Groq
limits actually bite — `ModelFallbackMiddleware` already exists, so nothing
needs building).

## 4. Layout

```
pyproject.toml           .env.example
corpus/                  sparse clone of Temporal docs (gitignored)
ingest.py                load -> chunk -> embed -> persist, with metadata
retrieval.py             dense (v1); + BM25 hybrid (v2)
llm.py                   model + rate limiter, ~15 lines
graph_v0.py              no retrieval — contamination baseline
graph_v1.py              retrieve -> generate
graph_v2.py              + grading, rewrite cycle, refusal
graph_v3.py              + routing, ACLs, memory
evals/golden.jsonl       40 questions
evals/run_eval.py        any graph -> LangSmith
evals/compare.py         the table
test_graph.py            one runnable check
```

**Load-bearing constraint:** every `graph_*.py` exports `graph` with an
identical invoke signature. That single rule turns cross-version comparison
into a for-loop. It is the reason for separate files rather than one evolving
graph or a flag matrix — checked-out history cannot be compared in one pass,
and feature flags make results ambiguous to interpret.

## 5. State and graphs

```python
class QAState(TypedDict):
    question: str
    documents: list[Document]
    generation: str
    retries: int
```

`retries` is unused before v2, declared now so v2 needs no state migration.

**v0** — `question -> LLM -> answer`. No retrieval. ~15 lines.

**v1** — `retrieve -> generate`. Two nodes, no branching. Deliberately
unsophisticated: it is the control group, and quality added here is quality
v2 cannot claim. Teaches `StateGraph`, node signatures, `.compile()`,
tracing.

**v2** — Corrective-RAG shaped. `grade_documents` as a conditional edge;
`rewrite_question` cycling back to retrieve, capped at 2 retries via
`state["retries"]`; a groundedness grader; an explicit refusal node. Hybrid
BM25 + dense retrieval. This is where conditional edges and cycles — the
transferable core — are learned.

**v3** — Adaptive-RAG complexity router, ACL filtering with a multi-tenant
eval, checkpointer-backed conversational memory. A subgraph or supervisor
only if a second corpus genuinely requires different retrieval; multi-agent
structure is not a goal in itself.

Chunking: recursive character splitting, ~300 tokens, 15% overlap, with the
markdown heading chain preserved as metadata. Fixed-size splitting is the
evidence-backed default; semantic chunking is not attempted.

Every chunk carries `permitted_roles` from ingestion onward. It is one dict
key, unenforced until v3, and retrofitting metadata after indexing means
re-embedding the corpus.

## 6. Evaluation

40 questions, stratified:

| Bucket | Tests |
|---|---|
| Direct lookup | baseline sanity |
| Jargon / acronym | hybrid retrieval (v2) |
| Multi-hop | routing and iterative retrieval (v3) |
| **Unanswerable** | hallucination vs. refusal |
| Ambiguous phrasing | query rewrite (v2) |

The unanswerable bucket is the most important and the most often skipped. It
produces the project's headline finding — the difference between fabricating
an answer and declining to. That sentence carries more weight than the graph
code.

**Metrics:** correctness (LLM judge vs. reference), faithfulness (against
retrieved context), retrieval recall@k. Retrieval and generation are scored
**separately**, so a regression identifies which half broke.

**v0 as ablation.** Running the golden set with no retrieval is standard
practice and simultaneously settles the corpus question with data. If v0
scores well, the corpus is contaminated and ~20 synthetic internal documents
get layered in — a fix applied to a measured problem rather than a
speculated one.

**Trace budget.** LangSmith's free tier is ~5,000 traces/month; a v2 eval run
is ~200+. That is roughly 25 full runs. Sample during iteration; run the
full set at phase gates.

## 7. Phase gates

v1 is not complete when it answers a question. It is complete when
`run_eval.py` has run all 40 and the baseline numbers are committed. **No v2
code before that table exists.**

This gate is the discipline the project exists to practice: complexity is
added in response to a measured deficiency, never in anticipation of one.
If context recall is already high and answers are still wrong, the fault is
generation, and more graph structure will not fix it.

Each phase: build -> eval -> record -> decide -> next.

## 8. Testing

One `test_graph.py`, assert-based, no framework. Covers: each graph compiles
and exposes the shared signature; retrieval returns non-empty results for a
known term; an unanswerable question yields refusal rather than fabrication.
The third assertion is the one that matters — it is the project's central
behavioral claim, and it must fail loudly if it regresses.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Corpus contamination | v0 baseline measures it; synthetic layer if confirmed |
| Golden set quality | Candidates drafted from corpus; **answers must be human-verified** — an unverified golden set measures nothing |
| Groq rate limits | `InMemoryRateLimiter`; fallback exists off-the-shelf if needed |
| LangSmith trace budget | Sample while iterating, full runs at gates |
| Python 3.14 wheels | Pin 3.12 at project init |
| v2 shows no gain over v1 | A legitimate finding, not a failure — provided evals are trustworthy. Report it. |
