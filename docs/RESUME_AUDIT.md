# Résumé claims versus the stable project

Reviewed on 18 October 2026 against implementation `b024062` and the current stable documentation checkpoint. This review covers the project excerpt supplied by the owner, not the rest of the résumé. Feature judgments come from code, the compiled graph, declared dependencies and tests. An engineering score is not an answer-accuracy measurement.

## Supplied project entry

> Multi-Agent QA System — github.com/kuntalashivasairahul/MultiAgent_QA_System 2025
>
> LangGraph, FastAPI, Groq LLaMA, Python
>
> Built a three-agent pipeline — Retrieval, Reasoning, and a Judge that scores answer quality and triggers a retrieval retry when confidence falls below a threshold.
>
> Orchestrated agent communication and conditional branching in LangGraph; exposed the pipeline through FastAPI REST endpoints.

## Claim-by-claim verdict

| Claim | Verdict | Actual implementation and evidence |
|---|---|---|
| LangGraph and Python | Supported | `graph_v2.build_graph` builds a typed `StateGraph`; `graph_v2_1.build_graph` reuses it with hybrid retrieval. Python 3.12 and LangGraph are declared in [pyproject.toml](../pyproject.toml). |
| Retrieval, Reasoning and Judge roles | Partially supported; wording overstates agent architecture | [graph_v2_1.py](../graph_v2_1.py) retrieves evidence, [graph_v1.py](../graph_v1.py) generates an answer, and [graph_v2.py](../graph_v2.py) performs LLM evidence checks. These are role-specific nodes/functions in a bounded workflow. Separate autonomous agents, inter-agent messaging infrastructure and a supervisor are not implemented. “LangGraph RAG workflow with retrieval, generation and evidence checking” is accurate now. |
| Judge scores answer quality | Qualitative checks implemented; numeric score missing | `EvidenceCheck` has exactly `passed`, `reason` and `quotes`. Sufficiency and support are boolean semantic verdicts. Aggregate evaluation metrics are separate from an in-graph answer-quality/confidence score. |
| Low-confidence threshold triggers retrieval retry | Missing | Compiled edges are START → retrieve → sufficient → generate/refuse; generate → supported → END. No downstream edge returns to retrieve. No numeric confidence/threshold field exists. The three-attempt quote-verdict correction and provider-error resumption repair validation/operations; neither retrieves new evidence after low answer quality. |
| Agent communication in LangGraph | State handoff supported; terminology needs qualification | Typed state carries question, documents, generation, citations and gate audits between nodes. This supports “orchestrated state handoff between workflow nodes”; it does not establish a separate agent messaging system. |
| Conditional branching in LangGraph | Supported | `graph_v2.build_graph` routes sufficiency pass to generation and failure to refusal. Support failure also produces the canonical refusal. A quality-driven retry branch is still missing. |
| FastAPI REST endpoints | Missing | No application/router/HTTP endpoint implementation exists in tracked application source. FastAPI and Uvicorn are not declared project dependencies. Invocation is through Python graph objects and evaluation CLIs. An incidental transitive package would not establish an implemented API. |
| Groq LLaMA | Historical configuration, outdated as the current stack | Initial commit `d5fd31f` configured `llama-3.3-70b-versatile`; `7a279e3` changed the default. Current [llm.py](../llm.py) defaults to GPT-OSS-120B generation and Qwen3.8-27B grading through Groq. Existing environment overrides remain possible; the retained tested final profile selects these models explicitly. Use “Groq-hosted LLMs” for the current project. |
| Project year 2025 | Not corroborated by repository evidence | The earliest available Git commit is `1c8c47c`, dated 1 September 2026. Git history does not prove when uncommitted/offline work began. Use the actual work dates; this review cannot validate 2025. |

## Wording supported now

**Temporal QA / RAG Evaluation — Python, LangGraph, Groq, Chroma, sentence-transformers**

- Built a versioned LangGraph RAG workflow over pinned Temporal documentation, combining dense and lexical retrieval with structured citations and LLM checks for evidence sufficiency and answer support.
- Implemented conditional answer/refusal routing and resumable evaluations with input fingerprints, retained judge evidence and SQLite graph checkpoints; verified 110 automated tests, including four corpus/index integration tests.

Keep the existing repository name/link if desired. Use accurate dates. Do not add FastAPI, confidence-triggered retrieval retries or a numerical accuracy improvement until implemented and measured. The 8.63/10 score is a coding-assistant engineering assessment and is unsuitable as a model-accuracy résumé metric.

## Verification and limits

- Fresh local full suite: **110 passed in 12.51s**, including four integration tests; `uv sync --frozen` checked 124 packages.
- Compiled graph inspection confirms the conditional generation/refusal branch and absence of a retrieval retry edge. Schema inspection confirms no quality-score/confidence field.
- Evaluation and comparison CLI help commands succeed. No new provider inference was requested for this résumé/release audit.
- The prior frozen checkout passed 106 offline tests without credentials/corpus/index; this is retained evidence and reused installed dependencies, not a new clean installation in this audit.
- Current final native development 40 and confirmation 12 remain unrun after the final code fix. The preceding implementation has only 21/40 scored development rows; those partial results cannot be presented as current full accuracy.
- Windows, independent review and production deployment are unverified. Hosted [GitHub CI run 39108281218](https://github.com/kuntalashivasairahul/MultiAgent_QA_System/actions/runs/39108281218) passed: 106 offline tests, fresh 14,414-document index and four integration tests; details are in the [release verification](../evals/results/stable_v21_release_verification.json).

The [v3 implementation plan](V3_RESUME_ALIGNMENT_PLAN.md) addresses the missing claims. Those features are planned, not included in the stable v2.1 push. See [current verification status](../evals/V21_FINAL_STATUS.md) for the stopped evaluation and retained evidence.
