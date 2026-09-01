# MultiAgent QA System — v1 Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A working RAG Q&A system over Temporal's docs, with a v0 no-retrieval
baseline and a v1 linear graph, both scored on the same 40-question golden set.

**Architecture:** LangGraph `StateGraph` over a Chroma index of Temporal's
markdown docs. Local BGE embeddings, Groq for generation. Every graph module
exports `graph` with an identical invoke signature so one eval script runs all
versions and emits a comparison table.

**Tech Stack:** Python 3.12 (uv), langgraph, langchain-groq,
langchain-huggingface + sentence-transformers, langchain-chroma, langsmith.

**Spec:** `docs/superpowers/specs/2026-09-01-multiagent-qa-design.md`

## Global Constraints

- Python **3.12** exactly — 3.14 breaks torch/sentence-transformers wheels.
- Every `graph_*.py` exports a module-level `graph` accepting
  `{"question": str}` and returning a state containing `generation` and
  `documents`. Non-negotiable — `compare.py` depends on it.
- Every chunk carries `permitted_roles` metadata from ingestion onward,
  unenforced until v3.
- LangSmith tracing enabled from the first commit, never retrofitted.
- **No v2 code until v1's baseline table is committed.**
- Embeddings run locally; only generation calls the network.

---

### Task 1: Project scaffolding

**Files:** Create `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`

- [ ] **Step 1: Init git and uv project pinned to 3.12**
```bash
git init
uv init --python 3.12 --no-workspace --bare
uv python pin 3.12
```
- [ ] **Step 2: Add dependencies**
```bash
uv add langgraph langchain langchain-core langchain-groq \
       langchain-huggingface langchain-chroma langchain-text-splitters \
       sentence-transformers langsmith python-dotenv
```
- [ ] **Step 3: Verify the interpreter is 3.12, not 3.14**
Run: `uv run python -c "import sys; print(sys.version)"`
Expected: `3.12.x`
- [ ] **Step 4: Write `.gitignore`**
```
.venv/
corpus/
chroma_db/
.env
__pycache__/
*.pyc
```
- [ ] **Step 5: Write `.env.example`**
```
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_RPS=0.4
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=multiagent-qa
```
- [ ] **Step 6: Commit**
```bash
git add -A && git commit -m "chore: scaffold project on python 3.12"
```

---

### Task 2: Corpus fetch

**Files:** Create `fetch_corpus.sh`

**Interfaces:**
- Produces: `corpus/docs/**/*.{md,mdx}` — ~767 files, ~892k words.

- [ ] **Step 1: Write `fetch_corpus.sh`**
```bash
#!/usr/bin/env bash
set -euo pipefail
rm -rf corpus
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/temporalio/documentation.git corpus
git -C corpus sparse-checkout set docs
echo "files: $(find corpus/docs -name '*.md*' | wc -l)"
```
- [ ] **Step 2: Run it**
Run: `chmod +x fetch_corpus.sh && ./fetch_corpus.sh`
Expected: `files: 7xx`
- [ ] **Step 3: Commit**
```bash
git add fetch_corpus.sh && git commit -m "feat: add corpus fetch script"
```

---

### Task 3: Ingestion

**Files:** Create `ingest.py`

**Interfaces:**
- Produces: `clean_mdx(text: str) -> str`, `load_chunks() -> list[Document]`,
  `build_index() -> Chroma`, `get_vectorstore() -> Chroma`,
  `EMBED_MODEL = "BAAI/bge-small-en-v1.5"`, persisted at `chroma_db/`.
- Chunk metadata keys: `source`, `headings`, `permitted_roles`.

- [ ] **Step 1: Write failing test in `test_graph.py`**
```python
from ingest import clean_mdx

def test_clean_mdx_strips_frontmatter_and_imports():
    raw = '---\ntitle: X\n---\nimport A from "b";\n\n# Head\nReal text.'
    out = clean_mdx(raw)
    assert "title: X" not in out
    assert "import A" not in out
    assert "Real text." in out
```
- [ ] **Step 2: Run and verify it fails**
Run: `uv run pytest test_graph.py -v` (or `uv run python test_graph.py`)
Expected: FAIL — `ImportError: cannot import name 'clean_mdx'`
- [ ] **Step 3: Implement `clean_mdx`, then `load_chunks` and `build_index`**
Cleaning: strip YAML frontmatter, `import`/`export` lines, JSX tags.
Splitting: `MarkdownHeaderTextSplitter` on `#`/`##`/`###` to capture the
heading chain, then `RecursiveCharacterTextSplitter(chunk_size=1200,
chunk_overlap=180)`. Set `permitted_roles: "all"` on every chunk.
- [ ] **Step 4: Run test, verify passes**
- [ ] **Step 5: Build the real index**
Run: `uv run python ingest.py`
Expected: chunk count printed (~4-6k), `chroma_db/` created.
- [ ] **Step 6: Commit**

---

### Task 4: Model wiring

**Files:** Create `llm.py`

**Interfaces:**
- Produces: `get_llm(temperature: float = 0.0) -> BaseChatModel`

- [ ] **Step 1: Implement**
```python
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv()

def get_llm(temperature: float = 0.0):
    return init_chat_model(
        os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        model_provider="groq",
        temperature=temperature,
        rate_limiter=InMemoryRateLimiter(
            requests_per_second=float(os.environ.get("GROQ_RPS", 0.4)),
            check_every_n_seconds=0.1,
            max_bucket_size=5,
        ),
    )
```
- [ ] **Step 2: Smoke test**
Run: `uv run python -c "from llm import get_llm; print(get_llm().invoke('say ok').content)"`
Expected: a short reply. If the model name 404s, adjust `GROQ_MODEL` in `.env`.
- [ ] **Step 3: Commit**

---

### Task 5: v0 — the no-retrieval baseline

**Files:** Create `graph_v0.py`

**Interfaces:**
- Consumes: `get_llm` from Task 4.
- Produces: module-level `graph`; `QAState` TypedDict with keys
  `question, documents, generation, retries`.

- [ ] **Step 1: Write failing test**
```python
def test_v0_graph_exposes_shared_interface():
    from graph_v0 import graph
    out = graph.invoke({"question": "What is a task queue?"})
    assert isinstance(out["generation"], str) and out["generation"]
    assert out["documents"] == []
```
- [ ] **Step 2: Run, verify fails**
- [ ] **Step 3: Implement** — one `answer` node, `START -> answer -> END`.
Prompt instructs: answer from your own knowledge; say "I don't know" if unsure.
`documents` always `[]`.
- [ ] **Step 4: Run, verify passes**
- [ ] **Step 5: Commit**

---

### Task 6: Retrieval and the v1 graph

**Files:** Create `retrieval.py`, `graph_v1.py`

**Interfaces:**
- Consumes: `get_vectorstore` (Task 3), `get_llm` (Task 4), `QAState` shape.
- Produces: `get_retriever(k: int = 5)`; `graph` in `graph_v1.py`.

- [ ] **Step 1: Write failing tests**
```python
def test_retriever_finds_jargon_term():
    from retrieval import get_retriever
    docs = get_retriever().invoke("continue-as-new")
    assert docs and any("continue" in d.page_content.lower() for d in docs)

def test_v1_retrieves_then_answers():
    from graph_v1 import graph
    out = graph.invoke({"question": "What is a Temporal task queue?"})
    assert out["documents"]
    assert out["generation"]
```
- [ ] **Step 2: Run, verify fails**
- [ ] **Step 3: Implement** — `retrieve` node fills `documents`; `generate`
node formats them into a grounded prompt. `START -> retrieve -> generate -> END`.
No branching. Deliberately minimal: this is the control group.
- [ ] **Step 4: Run, verify passes**
- [ ] **Step 5: Commit**

---

### Task 7: Golden dataset

**Files:** Create `evals/golden.jsonl`, `evals/draft_golden.py`

**Interfaces:**
- Produces: JSONL rows `{"question", "answer", "bucket", "source"}` with
  `bucket` in `direct | jargon | multihop | unanswerable | ambiguous`.

- [ ] **Step 1: Write `draft_golden.py`** — samples corpus chunks, asks the LLM
to propose question/answer pairs per bucket, writes `golden.draft.jsonl`.
Unanswerable questions are authored by hand, not sampled — they must be
plausible-but-absent, e.g. Temporal's pricing tiers.
- [ ] **Step 2: Generate drafts**
Run: `uv run python evals/draft_golden.py`
- [ ] **Step 3: HUMAN GATE — verify every answer against the corpus.**
Rename to `golden.jsonl` only after checking. An unverified golden set makes
every number downstream meaningless. Target 40: 12 direct, 8 jargon,
8 multihop, 8 unanswerable, 4 ambiguous.
- [ ] **Step 4: Commit**

---

### Task 8: Eval runner

**Files:** Create `evals/run_eval.py`

**Interfaces:**
- Consumes: any `graph_*` module by name; `golden.jsonl`.
- Produces: `run_eval(graph_module: str, limit: int | None) -> dict` with keys
  `correctness`, `faithfulness`, `recall_at_k`, `refusal_rate`; writes
  `evals/results/<module>.json`.

- [ ] **Step 1: Write failing test**
```python
def test_eval_scores_a_tiny_slice():
    from evals.run_eval import run_eval
    r = run_eval("graph_v0", limit=2)
    assert 0.0 <= r["correctness"] <= 1.0
```
- [ ] **Step 2: Run, verify fails**
- [ ] **Step 3: Implement** — LLM-as-judge for correctness (vs reference) and
faithfulness (vs retrieved context, auto-1.0 for v0 which has no context);
`recall_at_k` checks whether the golden `source` path appears in retrieved
metadata; `refusal_rate` measured on the unanswerable bucket only.
Scored **separately** so regressions localize to retrieval or generation.
- [ ] **Step 4: Run, verify passes**
- [ ] **Step 5: Commit**

---

### Task 9: Comparison table

**Files:** Create `evals/compare.py`

- [ ] **Step 1: Implement** — loop over available `graph_v*` modules, load or
run results, print a markdown table, write `evals/RESULTS.md`.
- [ ] **Step 2: Run the full baseline**
Run: `uv run python evals/compare.py`
Expected: table with v0 and v1 rows across all four metrics.
- [ ] **Step 3: Interpret the v0 row — the contamination check.**
v0 correctness high → corpus is contaminated, add synthetic docs per spec §6.
v0 correctness low, v1 much higher → retrieval is working; proceed to v2.
- [ ] **Step 4: Commit `evals/RESULTS.md`. This is the v1 phase gate.**

---

### Task 10: Documentation

**Files:** Modify `README.md`; create `docs/architecture.md`, `docs/journal.md`

- [ ] **Step 1: README** — what it is, setup, commands, current results table.
- [ ] **Step 2: `docs/architecture.md`** — graph diagrams per version, state
schema, ingestion flow, why separate graph files.
- [ ] **Step 3: `docs/journal.md`** — dated entries per phase: what was built,
what the numbers said, what was decided next. This is the artifact that shows
judgment rather than just output.
- [ ] **Step 4: Commit**

---

## Self-Review

**Spec coverage:** §2 corpus → Task 2. §3 stack → Tasks 1, 3, 4. §4 layout →
all. §5 state/graphs → Tasks 5, 6 (v2/v3 correctly out of scope). §6 eval →
Tasks 7, 8, 9. §7 gate → Task 9 Step 4. §8 testing → tests embedded per task.
§9 risks → contamination (T9 S3), golden verification (T7 S3), rate limits
(T4), Python version (T1 S3).

**Placeholders:** none — every step names a command, a file, or code.

**Type consistency:** `QAState` defined in Task 5, reused in Task 6.
`get_vectorstore`/`get_retriever`/`get_llm` names consistent across Tasks 3-6.
`graph` module-level export identical in Tasks 5, 6, and consumed in 8, 9.
