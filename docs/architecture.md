# Architecture

## Ingestion

```
corpus/docs/**/*.mdx
   → clean_mdx()          strip frontmatter, imports, JSX tags
   → MarkdownHeaderSplit  capture h1 > h2 > h3 chain as metadata
   → RecursiveCharSplit   1200 chars, 180 overlap
   → BGE-small (local)    384-dim, normalised
   → Chroma               chroma_db/, 9,765 chunks from 762 files
```

**Why code fences are protected.** `clean_mdx` splits on ``` and only cleans the
prose segments. Java and Rust generics (`List<String>`) are indistinguishable from
JSX tags to a regex, and the corpus contains 97 of them. Stripping them would
silently corrupt exactly the code samples that answer developer questions.

**Chunk metadata:** `source`, `title`, `headings`, `permitted_roles`.
`permitted_roles` is unenforced until v3 and is written now because retrofitting
metadata after indexing means re-embedding all 9,765 chunks.

## State

```python
class QAState(TypedDict, total=False):
    question: str
    documents: list[Document]
    generation: str
    retries: int        # unused before v2, declared now to avoid migration
```

Lives in `state.py`, shared by every version.

## Graphs

```
v0:  START → answer → END                        (documents always [])

v1:  START → retrieve → generate → END

v2:  START → retrieve → grade_documents → generate → check_grounded → END
                ↑              ↓                          ↓
                └── rewrite ───┘                       refuse
             (cycle, capped at 2 via state["retries"])
```

**Why separate files rather than one evolving graph.** Every `graph_v*.py` exports a
module-level `graph` taking `{"question": str}`. That single contract lets
`compare.py` score all versions in one pass. Git history cannot be compared without
checking out, and feature flags make results ambiguous to attribute — both defeat the
one artifact the project exists to produce.

`test_graph.py` asserts this contract directly.

## Evaluation

Retrieval and generation are scored separately so a regression localises:

| Metric | Measures | Method |
|---|---|---|
| `correctness` | answer vs. reference | LLM judge |
| `faithfulness` | answer vs. retrieved context | LLM judge |
| `recall_at_k` | did we retrieve the right doc | exact source-path match |
| `refusal_rate` | declining vs. fabricating | string match, no judge |

`refusal_rate` is deterministic on purpose — the project's headline claim should not
depend on judge variance.

## Cost

- Full eval run ≈ 40 questions × ~3 calls = ~120 Groq calls per version.
- Throttled to 0.4 req/s (`InMemoryRateLimiter`) → roughly 5 minutes per version.
- LangSmith free tier is ~5,000 traces/month. Sample while iterating; run the full
  set at phase gates only.
