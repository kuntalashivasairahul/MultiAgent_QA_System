# MultiAgent QA System

A retrieval-augmented Q&A system over [Temporal's](https://temporal.io) documentation,
built on LangGraph — and, more to the point, an experiment in whether added graph
complexity actually improves answers.

Each version is a separate graph scored on the same 40 questions. The output that
matters is not the chatbot; it is [`evals/RESULTS.md`](evals/RESULTS.md).

| Version | What it does | Status |
|---|---|---|
| **v0** | No retrieval — asks the model directly | built |
| **v1** | `retrieve → generate`, no branching | built |
| v2 | Document grading, query rewrite loop, refusal, hybrid search | not started |
| v3 | Complexity routing, ACL filtering, conversational memory | not started |

**v0 is not filler.** It measures whether the model already knows this corpus. If it
scores well, every retrieval number below it is measuring memorisation instead.

## Setup

```bash
uv sync                       # Python 3.12 — 3.14 breaks torch wheels
./fetch_corpus.sh             # sparse-clone Temporal docs (762 files, ~889k words)
uv run python ingest.py       # embed 9,765 chunks locally into chroma_db/ (~3 min)
cp .env.example .env          # then paste your Groq key
```

Embeddings run locally on CPU (`BAAI/bge-small-en-v1.5`) — no key, no quota.
Only generation calls the network.

## Use

```bash
uv run python test_graph.py                    # the check
uv run python evals/draft_golden.py            # draft golden-set candidates
uv run python evals/run_eval.py graph_v1       # score one version
uv run python evals/compare.py                 # build the comparison table
```

## The rule this project runs on

**No v2 code until v1's numbers are committed.** Complexity gets added in response to
a measured deficiency, never in anticipation of one. If context recall is already high
and answers are still wrong, the fault is in generation and more graph structure will
not fix it.

## Docs

- [Architecture](docs/architecture.md) — graph shapes, state, ingestion
- [Journal](docs/journal.md) — what was built, what the numbers said, what was decided
- [Design spec](docs/superpowers/specs/2026-09-01-multiagent-qa-design.md)
- [v1 plan](docs/superpowers/plans/2026-09-01-multiagent-qa-v1.md)
